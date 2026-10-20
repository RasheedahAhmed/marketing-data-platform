"""Dependency-free semantic check of project SQL using SQLite, not a dbt/Spark run.

The limited renderer understands only macros used by this project. It does not
replace dbt compilation, adapter validation, Delta tests, or Elementary execution.
Usage: python scripts/validate_local.py --fixtures fixtures
       python scripts/validate_local.py --raw-dir data/raw
"""
from pathlib import Path
import argparse, ast, csv, hashlib, json, re, sqlite3
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

ROOT=Path(__file__).resolve().parents[1]
FACT='fct_marketing_spend'

def safe_date(value):
    if value is None:return None
    try:return date.fromisoformat(value).isoformat()
    except (ValueError,TypeError):return None
def safe_timestamp(value):
    if value is None:return None
    try:return datetime.fromisoformat(value.replace('Z','+00:00')).isoformat()
    except (ValueError,TypeError):return None
def safe_bigint(value):
    if value is None or not re.fullmatch(r'[+-]?\d+',str(value)):return None
    n=int(value)
    return n if -(2**63)<=n<2**63 else None
def safe_decimal(value):
    if value is None:return None
    try:
        n=Decimal(value).quantize(Decimal('0.000001'),rounding=ROUND_HALF_UP)
        return float(n) if n.is_finite() and abs(n)<Decimal(10)**14 else None
    except (InvalidOperation,ValueError):return None

def key_sql(expressions):
    # Same length-prefixed, null-distinguishing serialization as macros.sk.
    return 'md5(concat('+','.join("case when {x} is null then 'N;' else concat('V', cast(length(cast({x} as text)) as text), ':', cast({x} as text), ';') end".format(x=x) for x in expressions)+'))'

def render(sql,incremental=False):
    sql=re.sub(r'\{% if is_incremental\(\) %\}(.*?)\{% endif %\}',lambda m:m[1] if incremental else '',sql,flags=re.S)
    def expression(m):
        s=m[1].strip()
        if s.startswith('config('):return ''
        if s=='this':return FACT
        if s.startswith('ref('):return ast.literal_eval(s[4:-1])
        if s.startswith('snapshot('):return 'bronze_'+ast.literal_eval(s[9:-1])
        if s.startswith('clean('):
            c=ast.literal_eval(s[6:-1])
            return f"nullif(nullif(trim(cast({c} as text)), ''), 'null')"
        if s.startswith('sk('):return key_sql(ast.literal_eval(s[3:-1]))
        raise ValueError('Unsupported template expression: '+s)
    sql=re.sub(r'\{\{(.*?)\}\}',expression,sql,flags=re.S)
    if '{{' in sql or '{%' in sql:raise ValueError('Unrendered template content')
    sql=re.sub(r'\bas string\b','as text',sql,flags=re.I)
    # Rewrite TRY_CAST with balanced parentheses to honest SQLite safe-cast UDFs.
    while (m:=re.search(r'\btry_cast\s*\(',sql,re.I)):
        start=m.end();depth=1;quote=False;i=start
        while depth:
            c=sql[i]
            if c=="'":quote=not quote
            if not quote:
                if c=='(':depth+=1
                elif c==')':depth-=1
            i+=1
        body=sql[start:i-1]
        value,typ=re.split(r'\s+as\s+',body,flags=re.I)[-2:]
        # The last AS separates the type; inner CAST AS text is retained.
        type_match=re.search(r'\s+as\s+(date|timestamp|bigint|decimal\(20,6\))\s*$',body,re.I)
        if not type_match:raise ValueError('Unsupported TRY_CAST '+body)
        value=body[:type_match.start()];typ=type_match[1].lower().split('(')[0]
        sql=sql[:m.start()]+'safe_'+typ+'('+value+')'+sql[i:]
    return sql

def connect():
    db=sqlite3.connect(':memory:')
    db.create_function('concat',-1,lambda *values:''.join('' if v is None else str(v) for v in values))
    db.create_function('md5',1,lambda v:hashlib.md5(v.encode()).hexdigest())
    for typ,fn in [('date',safe_date),('timestamp',safe_timestamp),('bigint',safe_bigint),('decimal',safe_decimal)]:db.create_function('safe_'+typ,1,fn)
    return db

def read_tables(args):
    specs=json.loads((ROOT/'config/sources.json').read_text())
    tables={}
    for name,spec in specs.items():
        if args.inspection_cache:
            p=Path(args.inspection_cache)/(spec['file']+'.jsonl')
            with p.open(encoding='utf-8') as f:
                header=json.loads(next(f))['headers']
                rows=[dict(zip(header,json.loads(line))) for line in f if line.strip()]
        else:
            path=Path(args.raw_dir or args.fixtures)/spec['file']
            with path.open(newline='',encoding='utf-8-sig') as f:
                reader=csv.DictReader(f);header=reader.fieldnames;rows=list(reader)
        if header!=spec['columns']:raise AssertionError('Header mismatch: '+name)
        if not rows:raise AssertionError('Empty source: '+name)
        tables[name]=rows
    return specs,tables

def load(db,specs,tables):
    for name,rows in tables.items():
        fields=specs[name]['columns']
        db.execute('create table bronze_'+name+' ('+','.join('"'+c+'" text' for c in fields+['_batch_id','_row_hash'])+')')
        values=[]
        for r in rows:
            v=[None if r[c] in ('','null','NULL') else r[c] for c in fields]
            h=hashlib.sha256(json.dumps(v,ensure_ascii=False).encode()).hexdigest()
            values.append(v+['a'*64,h])
        db.executemany('insert into bronze_'+name+' values ('+','.join('?' for _ in values[0])+')',values)

def build(db,models,incremental=False):
    pending=dict(models);order=[]
    while pending:
        progress=False
        for name,sql in list(pending.items()):
            dependencies=re.findall(r"ref\('([^']+)'\)",sql)
            if any(ref in pending for ref in dependencies):continue
            compiled=render(sql,incremental and name==FACT)
            if name==FACT and incremental:
                db.execute('drop table if exists next_fact')
                db.execute('create table next_fact as '+compiled)
                db.execute('drop table '+FACT)
                db.execute('alter table next_fact rename to '+FACT)
            else:
                db.execute('drop table if exists '+name)
                db.execute('create table '+name+' as '+compiled)
            order.append(name);del pending[name];progress=True
        if not progress:raise AssertionError('Model cycle or missing ref: '+str(pending.keys()))
    return order

def run_tests(db):
    results=[]
    for path in sorted((ROOT/'tests').glob('*.sql')):
        rows=db.execute(render(path.read_text())).fetchmany(5)
        results.append({'test':path.stem,'passed':not rows,'example_failures':rows})
    # Execute the built-in YAML tests represented in the model catalog.
    schema=json.loads((ROOT/'models/schema.yml').read_text())
    for model in schema['models']:
        for col in model['columns']:
            for test in col.get('data_tests',[]):
                name=model['name'];c=col['name']
                if test=='not_null':q=f'select {c} from {name} where {c} is null'
                elif test=='unique':q=f'select {c} from {name} group by {c} having count(*)>1'
                elif isinstance(test,dict) and 'accepted_values' in test:
                    vals=','.join("'"+v+"'" for v in test['accepted_values']['values'])
                    q=f'select {c} from {name} where {c} not in ({vals})'
                else:raise ValueError('Unsupported local built-in test '+str(test))
                rows=db.execute(q).fetchmany(5)
                results.append({'test':name+'.'+c+'.'+str(test),'passed':not rows,'example_failures':rows})
    return results

def main():
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--fixtures');g.add_argument('--raw-dir');g.add_argument('--inspection-cache')
    p.add_argument('--output',default='docs/local_validation.json')
    args=p.parse_args()
    specs,tables=read_tables(args)
    db=connect();load(db,specs,tables)
    models={p.stem:p.read_text() for p in (ROOT/'models').rglob('*.sql')}
    order=build(db,models);results=run_tests(db)
    totals=[dict(zip(['platform','currency_code','rows','spend','known_impressions','known_clicks','unknown_impression_rows','unknown_click_rows','first_day','last_day'],r)) for r in db.execute('select platform,currency_code,count(*),round(sum(spend),6),sum(impressions),sum(clicks),sum(impressions is null),sum(clicks is null),min(date_day),max(date_day) from marketing_performance group by platform,currency_code order by platform,currency_code')]
    initial_count=db.execute('select count(*) from marketing_performance').fetchone()[0]
    before=db.execute('select performance_key,spend from marketing_performance order by performance_key limit 1').fetchone()
    build(db,models,incremental=True)
    results.append({'test':'idempotent_rebuild','passed':db.execute('select count(*) from marketing_performance').fetchone()[0]==initial_count})
    # Historical correction is read even when it falls outside a recent-date window.
    db.execute("update bronze_facebook_stats set ad_spend='123.456789' where rowid=(select min(rowid) from bronze_facebook_stats)")
    build(db,models,incremental=True)
    corrected=db.execute('select spend from marketing_performance where platform=\'facebook\' and ad_id=(select ad_id from bronze_facebook_stats order by rowid limit 1) and date_day=(select ad_date from bronze_facebook_stats order by rowid limit 1) and account_id=(select account_id from bronze_facebook_stats order by rowid limit 1)').fetchone()
    results.append({'test':'historical_correction','passed':bool(corrected) and abs(corrected[0]-123.456789)<1e-8})
    # Removed keys become tombstones and disappear from the recommended view.
    db.execute('delete from bronze_facebook_stats where rowid=(select min(rowid) from bronze_facebook_stats)')
    build(db,models,incremental=True)
    results.append({'test':'snapshot_delete','passed':db.execute('select count(*) from marketing_performance').fetchone()[0]==initial_count-1 and db.execute('select count(*) from fct_marketing_spend where is_deleted').fetchone()[0]==1})
    # Deliberately break one parent relationship: facts must survive and quality must fail.
    db.execute('delete from bronze_snapchat_ads where ad_id=(select ad_detail_id from bronze_snapchat_stats limit 1)')
    build(db,models,incremental=True)
    results.append({'test':'orphan_preserved_and_detected','passed':db.execute('select count(*) from marketing_performance').fetchone()[0]==initial_count-1 and bool(db.execute(render((ROOT/'tests/complete_hierarchy.sql').read_text())).fetchone())})
    # A conflicting metric at the same natural key must be detected before MERGE.
    fields=specs['facebook_stats']['columns']+['_batch_id','_row_hash']
    db.execute('insert into bronze_facebook_stats select '+','.join("'999.0'" if c=='ad_spend' else ("'conflicting_payload'" if c=='_row_hash' else c) for c in fields)+' from bronze_facebook_stats limit 1')
    build(db,{k:v for k,v in models.items() if k.startswith('stg_')})
    results.append({'test':'conflicting_grain_detected','passed':bool(db.execute(render((ROOT/'tests/unique_facebook_stat_grain.sql').read_text())).fetchone())})
    report={'engine':'SQLite semantic SQL execution with a restricted renderer; NOT dbt compilation, Spark, Delta MERGE execution, or Elementary validation.','scope':'complete uploaded source tables' if args.inspection_cache or args.raw_dir else 'small linked source fixtures','source_rows':{k:len(v) for k,v in tables.items()},'model_order':order,'original_totals':totals,'checks':results,'passed':all(r['passed'] for r in results),'remaining':['Install and resolve pinned dbt/Elementary dependencies.','Run dbt parse and dbt build on Databricks.','Exercise physical Delta MERGE, permissions, and service-principal OAuth.','Generate real dbt static HTML and Elementary reports from warehouse runs.']}
    out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'passed':report['passed'],'checks':len(results),'source_rows':sum(report['source_rows'].values()),'models':len(order),'report':str(out)},indent=2))
    if not report['passed']:
        print(json.dumps([r for r in results if not r['passed']],indent=2));raise SystemExit(1)

if __name__=='__main__':main()

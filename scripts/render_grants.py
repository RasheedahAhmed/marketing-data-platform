"""Produce admin SQL; does not apply permissions or embed secrets."""
import argparse
import re
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--catalog',required=True)
p.add_argument('--schema-prefix',required=True,help='Exactly DBT_SCHEMA for this environment.')
p.add_argument('--principal',required=True,help='Databricks application ID or developer email.')
p.add_argument('--reader-group',default='marketing_analysts')
p.add_argument('--output',default='artifacts/bootstrap.sql')
a=p.parse_args()
for v in [a.catalog,a.schema_prefix]:
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*',v):raise SystemExit('Unsafe SQL identifier')
for v in [a.principal,a.reader_group]:
    if not v or '`' in v:raise SystemExit('Invalid principal')
c=a.catalog;principal='`'+a.principal+'`';readers='`'+a.reader_group+'`'
sql=[f'CREATE CATALOG IF NOT EXISTS {c};',f'GRANT USE CATALOG ON CATALOG {c} TO {principal};']

if c == 'marketing_ci':
    sql.append(f'GRANT CREATE SCHEMA ON CATALOG {c} TO {principal};')
schemas=['landing','bronze',a.schema_prefix,a.schema_prefix+'_staging',a.schema_prefix+'_marts',a.schema_prefix+'_elementary',a.schema_prefix+'_dbt_test__audit']
for schema in schemas:
    sql += [f'CREATE SCHEMA IF NOT EXISTS {c}.{schema};',f'GRANT USE SCHEMA ON SCHEMA {c}.{schema} TO {principal};']
for schema in ['bronze',a.schema_prefix,a.schema_prefix+'_staging',a.schema_prefix+'_marts',a.schema_prefix+'_elementary',a.schema_prefix+'_dbt_test__audit']:
    for privilege in ['CREATE TABLE','SELECT','MODIFY']:
        sql.append(f'GRANT {privilege} ON SCHEMA {c}.{schema} TO {principal};')
sql += [f'CREATE VOLUME IF NOT EXISTS {c}.landing.marketing_files;',f'GRANT READ VOLUME ON VOLUME {c}.landing.marketing_files TO {principal};',
        f'GRANT USE CATALOG ON CATALOG {c} TO {readers};',f'GRANT USE SCHEMA ON SCHEMA {c}.{a.schema_prefix}_marts TO {readers};',
        '-- Grant readers only approved active reporting views AFTER the build:']
for view in ['marketing_performance','rpt_campaign_daily','dim_campaigns']:
    sql.append(f'GRANT SELECT ON VIEW {c}.{a.schema_prefix}_marts.{view} TO {readers};' if view!='dim_campaigns' else f'GRANT SELECT ON TABLE {c}.{a.schema_prefix}_marts.{view} TO {readers};')
dest=Path(a.output);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text('\n'.join(sql)+'\n')
print(dest)

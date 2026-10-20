"""Run from the project root. Only source reads are pinned; target writes remain serialized."""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

def run(args, capture=False):
    executable=shutil.which('dbt')
    if not executable: raise SystemExit('Activate the virtual environment containing dbt first.')
    return subprocess.run([executable,*args],check=True,text=True,stdout=subprocess.PIPE if capture else None, stderr=subprocess.STDOUT)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--target',choices=['dev','staging','ci','prod'],default='dev')
    parser.add_argument('--full-refresh',action='store_true')
    args=parser.parse_args()
    if args.target != 'dev':
        for key in ['DATABRICKS_CLIENT_ID','DBT_ENV_SECRET_DATABRICKS_CLIENT_SECRET']:
            if not os.environ.get(key):
                raise SystemExit(f'{key} is required for non-interactive service-principal OAuth.')
    base=['--profiles-dir','profiles','--target',args.target]
    run(['deps',*base])
    result=run(['run-operation','print_snapshot_id',*base],capture=True)
    match=re.search(r'SNAPSHOT_BATCH_ID=([0-9a-f]{64})',result.stdout)
    if not match:raise SystemExit('No valid published batch ID. Ingest the complete snapshot first.')
    batch_id=match.group(1)
    Path('artifacts').mkdir(exist_ok=True)
    Path('artifacts/snapshot.json').write_text(json.dumps({'target':args.target,'snapshot_batch_id':batch_id},indent=2))
    variables=json.dumps({'snapshot_batch_id':batch_id})
    pinned=[*base,'--vars',variables]
    # Build Elementary metadata tables before the first monitored project build.
    run(['run','--select','elementary',*pinned])
    run(['build',*pinned,*(['--full-refresh'] if args.full_refresh else [])])
    run(['docs','generate','--static',*pinned])
    print(f'Built and documented {args.target} from complete batch {batch_id}.')

if __name__=='__main__': main()


# Databricks notebook source
"""Load a complete nine-file snapshot. Run on Unity Catalog-enabled Python compute.
No cloud credentials are embedded. Runtime identity is the job run-as principal.
All files must be immutable during the run. Concurrency: one pipeline run per environment.
"""
import hashlib
import json
import re
from datetime import datetime, timezone
from pyspark.sql import functions as F
from delta.tables import DeltaTable

dbutils.widgets.text('catalog', 'marketing_dev')
dbutils.widgets.text('bronze_schema', 'bronze')
dbutils.widgets.text('input_path', '/Volumes/marketing_dev/landing/marketing_files')
catalog = dbutils.widgets.get('catalog')
schema = dbutils.widgets.get('bronze_schema')
input_path = dbutils.widgets.get('input_path').rstrip('/')
for value in [catalog, schema]:
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', value):
        raise ValueError('Catalog and schema must be safe SQL identifiers.')
if not input_path.startswith('/Volumes/'):
    raise ValueError('Upload the nine CSVs into a Unity Catalog Volume first.')
SOURCES = {'facebook_stats': {'file': 'ads_stats.csv', 'columns': ['ad_id', 'account_id', 'ad_spend', 'ad_impressions', 'ad_clicks', 'ad_date']}, 'facebook_ads': {'file': 'new_ads_de_randomized.csv', 'columns': ['ad_id', 'campaign_id', 'ad_group_id', 'account_id', 'ad_name', 'ad_status', 'ad_updated_at']}, 'facebook_adgroups': {'file': 'new_adgroup_de_randomized.csv', 'columns': ['ad_group_id', 'ad_group_name', 'ad_group_updated_at']}, 'facebook_campaigns': {'file': 'new_campaign_de_randomized.csv', 'columns': ['campaign_id', 'campaign_name', 'campaign_updated_at']}, 'facebook_accounts': {'file': 'new_acccount_de_randomized.csv', 'columns': ['account_id', 'account_name', 'ad_currency_code', 'account_created_at', 'account_updated_at']}, 'snapchat_stats': {'file': 'snapchat_ads_stats.csv', 'columns': ['ad_detail_id', 'ad_currency_code', 'ad_country', 'ad_spend', 'ad_impressions', 'ad_clicks', 'ad_date', 'data_src']}, 'snapchat_ads': {'file': 'snapchat_ads_ad_history_new_ad_names.csv', 'columns': ['ad_id', 'ad_group_id', 'ad_name', 'ad_detail_updated_at']}, 'snapchat_adgroups': {'file': 'snapchat_ads_adgroup_history_new_ad_group_names.csv', 'columns': ['_surrogate_key', 'ad_group_id', 'campaign_id', 'ad_group_name', 'ad_group_updated_at']}, 'snapchat_campaigns': {'file': 'snapchat_ads_campaign_history_new_campaign_names.csv', 'columns': ['campaign_id', 'account_id', 'campaign_name']}}
prefix = f'{catalog}.{schema}'
staged = {}
file_hashes = {}
counts = {}
loaded_at = datetime.now(timezone.utc).isoformat()

# Validate every header and read every complete extract before touching Bronze.
for name, spec in SOURCES.items():
    path = input_path + '/' + spec['file']
    before = spark.read.format('binaryFile').load(path).select(F.sha2('content',256).alias('sha')).collect()
    if len(before) != 1:
        raise ValueError(f'Expected one file: {path}')
    frame = (spark.read.option('header', True).option('inferSchema', False)
             .option('mode', 'FAILFAST').option('nullValue', 'null')
             .option('multiLine', True).option('escape', '"').csv(path))
    if frame.columns != spec['columns']:
        raise ValueError(f'Header mismatch in {spec["file"]}: {frame.columns}')
    # Spark infers CSV headers, but values are strings because inferSchema=False.
    frame = frame.select([F.col(c).cast('string').alias(c) for c in spec['columns']]).cache()
    counts[name] = frame.count()
    if counts[name] == 0:
        raise ValueError(f'Empty extract refused: {name}. Explicitly review before a full-snapshot delete.')
    after = spark.read.format('binaryFile').load(path).select(F.sha2('content',256).alias('sha')).first()['sha']
    if before[0]['sha'] != after:
        raise ValueError('Input changed during ingestion; publish immutable files and retry.')
    file_hashes[name] = after
    staged[name] = frame

batch_id = hashlib.sha256(json.dumps(file_hashes, sort_keys=True).encode()).hexdigest()
audit_rows = []
try:
    for name, frame in staged.items():
        frame = (frame.withColumn('_row_hash', F.sha2(F.to_json(F.struct(*[F.col(c) for c in SOURCES[name]['columns']]), {'ignoreNullFields':'false'}),256))
                 .withColumn('_batch_id', F.lit(batch_id))
                 .withColumn('_loaded_at', F.to_timestamp(F.lit(loaded_at)))
                 .withColumn('_source_file', F.lit(SOURCES[name]['file'])))
        table = f'{prefix}.raw__{name}'
        writer = frame.write.format('delta').mode('overwrite')
        if spark.catalog.tableExists(table):
            writer.option('replaceWhere', f"_batch_id = '{batch_id}'").saveAsTable(table)
        else:
            writer.partitionBy('_batch_id').saveAsTable(table)
        actual = spark.table(table).where(F.col('_batch_id')==batch_id).count()
        if actual != counts[name]:
            raise RuntimeError(f'Row-count mismatch in {table}')
        audit_rows.append((batch_id, name, SOURCES[name]['file'], file_hashes[name], counts[name], loaded_at))
    audit = spark.createDataFrame(audit_rows, 'batch_id string, source_name string, source_file string, file_sha256 string, row_count long, loaded_at_iso string')
    audit_table=f'{prefix}.batch_audit'
    writer=audit.write.format('delta').mode('overwrite')
    if spark.catalog.tableExists(audit_table):
        writer.option('replaceWhere', f"batch_id = '{batch_id}'").saveAsTable(audit_table)
    else:
        writer.partitionBy('batch_id').saveAsTable(audit_table)
    spark.sql(f"CREATE TABLE IF NOT EXISTS {prefix}.active_batch (dataset STRING, batch_id STRING, published_at TIMESTAMP) USING DELTA")
    pointer = spark.createDataFrame([('marketing',batch_id,loaded_at)], 'dataset string, batch_id string, published_at_iso string').select('dataset','batch_id',F.to_timestamp('published_at_iso').alias('published_at'))
    (DeltaTable.forName(spark,f'{prefix}.active_batch').alias('t').merge(pointer.alias('s'),'t.dataset = s.dataset')
     .whenMatchedUpdateAll().whenNotMatchedInsertAll().execute())
    # This atomic pointer update publishes all nine tables together.
    print(json.dumps({'batch_id':batch_id,'source_rows':counts,'status':'published'},indent=2))
finally:
    for frame in staged.values():
        frame.unpersist()

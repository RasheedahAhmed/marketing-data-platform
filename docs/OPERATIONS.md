# Operational decisions

## Publication, retry and rollback

All nine full CSVs belong to one immutable source snapshot. The ingestion notebook verifies the schema and hashes file contents before/after reading, writes raw batches idempotently with replaceWhere, checks row counts and publishes one active_batch pointer only after every source succeeds. If ingestion fails before publication, the previous pointer remains usable and the partial batch is not read by a normal build. Retry with immutable files; do not manually point at incomplete batches.

The dbt runner freezes a 64-character batch hash before invoking dbt build. All raw reads and tests use that ID. Avoid direct concurrent dbt writers. A pointer publication does not commit all marts atomically: refresh BI after the entire pipeline succeeds. For rollback, an operator can identify a previous complete batch in batch_audit and run dbt build with an explicitly pinned snapshot_batch_id and full refresh. Verify every source exists for that hash first. Retain raw snapshots for the required rollback window.

## Error handling

Malformed dates/numeric values, conflicting natural keys, dimension version conflicts and negative metrics are hard failures. Unmatched hierarchy records are retained in the model and normally fail complete_hierarchy. To inspect a degraded exploratory build only, set strict_relationships=false; the row-preserving SQL does not change. Fix the input or explain accepted exceptions before production publication. Do not silently drop rows, use campaign names as joins, or replace missing metrics with zeros.

## Freshness and scheduling

These are historical static extracts; no current-event-date freshness SLA is asserted. _loaded_at and active_batch.published_at record ingestion/publication, not the original source system extraction time. batch_audit records exactly what was loaded. Monitor scheduled ingestion failures and publication lag against your actual schedule. No source timestamp is invented. When regular extracts exist, add an ingestion freshness SLA and calibrate Elementary anomaly tests using that history.

## Scaling

The full snapshot scan is a deliberate correctness choice for approximately 95,000 fact observations. A scalable future version should use source revisions/change streams, reliable per-key update timestamps, late-arrival lookback plus backfill, explicit deletion events, automated API extraction and an FX dimension if cross-currency reporting is required. Keep country and currency in the fact grain. Add date clustering/partitioning only after examining actual query volume and data size.

## Security and artifacts

Credentials must remain in environment/secret stores. The production OAuth principal must have the expected workspace/warehouse/catalog rights. CI gets schema-creation rights only in its own catalog. Do not expose raw fact tables with deletion tombstones to general consumers. Test failures and HTML reports may contain source samples; keep CI artifacts private with an appropriate retention period. Never upload profiles containing literal secrets. The included workflow uploads target/artifacts only.

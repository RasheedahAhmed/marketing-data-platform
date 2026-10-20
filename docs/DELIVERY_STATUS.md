# Assignment delivery status

## Prepared in this package

- Source-specific Databricks ingestion notebook and nine-source manifest.
- dbt staging/intermediate/mart models and documented business grain.
- Automated quality SQL, model schema metadata, package configuration and static-doc generation command.
- Elementary dbt package, CLI profile and report generation command.
- CI/dev/staging/prod targets, production OAuth service-principal configuration, grants generator and GitHub Actions.
- Linked fixtures, actual-source profile, semantic SQL checker and validation reports.

## Still requires your Databricks/GitHub environment

- [ ] Install dependencies successfully; retain a resolved dependency lock.
- [ ] Create/confirm catalogs, schemas, Volume, SQL Warehouse and ingestion compute.
- [ ] Assign the real service principal and apply reviewed permissions.
- [ ] Upload and ingest all nine full CSV extracts; retain batch audit output.
- [ ] Run dbt debug using development OAuth and production service-principal OAuth.
- [ ] Run dbt parse and dbt build successfully on Databricks.
- [ ] Run a second build and exercise native Delta MERGE updates/deletes.
- [ ] Inspect generated target/static_index.html and lineage.
- [ ] Generate artifacts/elementary_report.html from real warehouse metadata.
- [ ] Execute repeat monitored builds to establish historical test results.
- [ ] Configure GitHub environment credentials and run PR/staging/production workflows.
- [ ] Grant analysts SELECT on the approved reporting views, then validate business queries.

Local SQLite results verify logical SQL behavior only. They do not establish that deployment, permissions, authentication, native adapter execution or observability has already succeeded.

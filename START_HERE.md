# Start here

The code package is ready for setup. To complete the assignment, run it in your Databricks workspace and retain the generated evidence.

## 1. Open the project and check it locally

Extract the ZIP and open its marketing_data_platform folder in VS Code. Python 3.11 is recommended. The offline check needs no packages:

```powershell
python scripts/validate_local.py --fixtures fixtures
```

Copy the nine original CSVs into data/raw for a full check:

```powershell
python scripts/validate_local.py --raw-dir data/raw --output docs/local_validation_full.json
```

## 2. Prepare Databricks

You need Unity Catalog, a SQL Warehouse and Unity Catalog-enabled Python notebook compute. An administrator creates the environment catalog and schemas, assigns your identity/service principal to the workspace and grants compute access.

Generate permission SQL using your actual developer email for development, or actual service-principal application ID for production. This only writes a reviewable SQL file:

```powershell
python scripts/render_grants.py --catalog marketing_dev --schema-prefix dev_rasheedah --principal YOUR_EMAIL --reader-group marketing_analysts
```

Replace YOUR_EMAIL and ensure the reader group exists. Have the administrator execute artifacts/bootstrap.sql. Run its final reporting-view grants after the first successful build. Repeat with marketing_staging / marketing_prod and schema prefix marketing for those environments; use their own principals. Do not reuse the example IDs in the assignment PDF.

## 3. Upload and ingest the source CSVs

In Catalog Explorer, open marketing_dev → landing → marketing_files and upload all nine original files with unchanged filenames. Import databricks/01_ingest_csv.py as a Databricks notebook. Run it with:

- catalog: marketing_dev
- bronze_schema: bronze
- input_path: /Volumes/marketing_dev/landing/marketing_files

The result prints a published batch ID and row counts. Inspect bronze.active_batch, bronze.batch_audit and the nine bronze.raw__* tables. Do not upload only a partial date extract; this implementation expects complete snapshots.

## 4. Install dbt and configure your connection

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:DBT_HOST = 'YOUR_WORKSPACE_HOST_WITHOUT_HTTPS'
$env:DBT_HTTP_PATH = '/sql/1.0/warehouses/YOUR_WAREHOUSE_ID'
$env:DBT_CATALOG = 'marketing_dev'
$env:DBT_SCHEMA = 'dev_rasheedah'
$env:BRONZE_CATALOG = 'marketing_dev'
$env:BRONZE_SCHEMA = 'bronze'
dbt debug --profiles-dir profiles --target dev
python scripts/run_dbt.py --target dev
```

Developer OAuth opens an interactive login. The build script installs the dbt package, freezes the raw snapshot ID, initializes Elementary, runs dbt build, and generates static dbt HTML. Check target/run_results.json and open target/static_index.html.

## 5. Configure production using a service principal

Create a Databricks service principal, assign it to the workspace, grant SQL Warehouse CAN USE and the reviewed Unity Catalog grants. Create its Databricks OAuth secret. Store the application ID and secret securely in your runtime environment; do not paste the secret into chat or commit it.

Set the production catalog/schema variables, then provide DATABRICKS_CLIENT_ID and DBT_ENV_SECRET_DATABRICKS_CLIENT_SECRET through your secret manager/shell. Run:

```powershell
python scripts/run_dbt.py --target prod
edr report --profiles-dir profiles --profile-target prod --project-profile-target prod --file-path artifacts/elementary_report.html
```

Create GitHub environments ci, staging and production as described in README.md, bootstrap their catalogs and initial source batches, and enable the included workflow in your repository. Use max_concurrent_runs=1 for the entire environment pipeline. Run BI refreshes only after success.

## What to submit

Submit this repository plus your actual successful warehouse artifacts: dbt run results, dbt static HTML, Elementary report, permission/authentication evidence with secrets hidden, and CI build evidence. docs/DELIVERY_STATUS.md lists the exact remaining verification items. The README explains the modeling decisions and source caveats.

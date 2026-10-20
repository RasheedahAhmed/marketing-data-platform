{% macro text_type() %}string{% endmacro %}

{% macro clean(column) -%}
nullif(nullif(trim(cast({{ column }} as string)), ''), 'null')
{%- endmacro %}

{% macro sk(expressions) -%}
md5(concat(
{%- for expression in expressions %}
    case when {{ expression }} is null then 'N;'
    else concat('V', cast(length(cast({{ expression }} as string)) as string), ':', cast({{ expression }} as string), ';') end{% if not loop.last %},{% endif %}
{%- endfor %}
))
{%- endmacro %}

{% macro snapshot(name) -%}
{% set frozen = var('snapshot_batch_id', '') %}
{% if frozen and not modules.re.fullmatch('[0-9a-f]{64}', frozen) %}
 {{ exceptions.raise_compiler_error('snapshot_batch_id must be a SHA-256 hex digest.') }}
{% endif %}
(select * from {{ source('bronze', name) }}
 where _batch_id =
 {% if var('snapshot_batch_id', '') %}
   '{{ var("snapshot_batch_id") }}'
 {% else %}
   (select batch_id from {{ source('bronze', 'active_batch') }} where dataset = 'marketing')
 {% endif %}
)
{%- endmacro %}

{% macro print_snapshot_id() %}
{% if execute %}
  {% set result = run_query("select batch_id from " ~ source('bronze','active_batch') ~ " where dataset = 'marketing'") %}
  {% if result.rows | length != 1 %}{{ exceptions.raise_compiler_error('Publish exactly one complete marketing batch first.') }}{% endif %}
  {{ log('SNAPSHOT_BATCH_ID=' ~ result.rows[0][0], info=true) }}
{% endif %}
{% endmacro %}

{% macro bootstrap_ci_schemas() %}
{% if target.name != 'ci' or not target.schema.startswith('ci_pr_') %}
 {{ exceptions.raise_compiler_error('CI bootstrap requires target ci and ci_pr_ schema prefix.') }}
{% endif %}
{% if execute %}
 {% for suffix in ['', '_staging', '_marts', '_elementary', '_dbt_test__audit'] %}
  {% do run_query('create schema if not exists ' ~ adapter.quote(target.database) ~ '.' ~ adapter.quote(target.schema ~ suffix)) %}
 {% endfor %}
{% endif %}
{% endmacro %}

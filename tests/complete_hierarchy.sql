{{ config(severity='error' if var('strict_relationships', true) else 'warn') }}
select performance_key from {{ ref('marketing_performance') }} where not hierarchy_complete

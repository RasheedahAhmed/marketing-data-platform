select 'mixed_batch' as issue, count(*) as rows_checked from {{ ref('marketing_performance') }} having count(distinct _batch_id) <> 1

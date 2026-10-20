{{ config(materialized='view') }}
select *,
 case when impressions > 0 and clicks is not null then cast(clicks as double) / impressions end as ctr,
 case when clicks > 0 then cast(spend as double) / clicks end as cpc,
 case when impressions > 0 then cast(spend as double) / impressions * 1000 end as cpm
from {{ ref('fct_marketing_spend') }} where not is_deleted

{{ config(materialized='view') }}
with totals as (
 select date_day, platform, account_id, campaign_id, campaign_key, campaign_name, currency_code,
 count(*) as source_rows, sum(spend) as spend,
 sum(impressions) as known_impressions, sum(clicks) as known_clicks,
 sum(case when impressions is null then 1 else 0 end) as unknown_impression_rows,
 sum(case when clicks is null then 1 else 0 end) as unknown_click_rows,
 case when count(impressions) = count(*) then sum(impressions) end as impressions,
 case when count(clicks) = count(*) then sum(clicks) end as clicks
 from {{ ref('marketing_performance') }}
 group by date_day, platform, account_id, campaign_id, campaign_key, campaign_name, currency_code
)
select *,
 case when impressions > 0 and clicks is not null then cast(clicks as double)/impressions end as ctr,
 case when clicks > 0 then cast(spend as double)/clicks end as cpc,
 case when impressions > 0 then cast(spend as double)/impressions * 1000 end as cpm
from totals

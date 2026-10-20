{{ config(materialized='incremental', incremental_strategy='merge', unique_key='performance_key', file_format='delta', on_schema_change='fail') }}
with current_rows as (
 select * from {{ ref('int_marketing_ads') }}
)
select performance_key, campaign_key, platform, date_day, account_id, ad_id, ad_group_id, campaign_id, ad_name, ad_group_name, campaign_name, account_name, ad_status, currency_code, country_code, spend, impressions, clicks, _batch_id, hierarchy_complete, false as is_deleted from current_rows
{% if is_incremental() %}
union all
select old.performance_key, old.campaign_key, old.platform, old.date_day, old.account_id, old.ad_id, old.ad_group_id, old.campaign_id, old.ad_name, old.ad_group_name, old.campaign_name, old.account_name, old.ad_status, old.currency_code, old.country_code, old.spend, old.impressions, old.clicks, old._batch_id, old.hierarchy_complete, true as is_deleted
from {{ this }} old
left join current_rows new on old.performance_key = new.performance_key
where new.performance_key is null
{% endif %}

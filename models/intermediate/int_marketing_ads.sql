with unified as (
 select s.platform, s.date_day, s.account_id, s.ad_id, a.ad_group_id, a.campaign_id,
 a.ad_name, a.ad_group_name, a.campaign_name, a.account_name, a.ad_status,
 a.currency_code, cast(null as string) as country_code,
 s.spend, s.impressions, s.clicks, s._batch_id,
 (a.ad_id is not null and a.hierarchy_complete) as hierarchy_complete
 from {{ ref('stg_facebook_stats') }} s
 left join {{ ref('int_facebook_ads') }} a on s.ad_id = a.ad_id and s.account_id = a.account_id
 union all
 select s.platform, s.date_day, a.account_id, s.ad_id, a.ad_group_id, a.campaign_id,
 a.ad_name, a.ad_group_name, a.campaign_name, a.account_name, a.ad_status,
 s.currency_code, s.country_code, s.spend, s.impressions, s.clicks, s._batch_id,
 (a.ad_id is not null and a.hierarchy_complete) as hierarchy_complete
 from {{ ref('stg_snapchat_stats') }} s
 left join {{ ref('int_snapchat_ads') }} a on s.ad_id = a.ad_id
)
select {{ sk(['platform','account_id','ad_id','date_day','country_code','currency_code']) }} as performance_key,
 case when campaign_id is not null then {{ sk(['platform','account_id','campaign_id']) }} end as campaign_key,
 * from unified

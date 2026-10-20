{{ config(materialized='table', file_format='delta') }}
with campaigns as (
 select distinct 'facebook' as platform, a.account_id, a.campaign_id, c.campaign_name
 from {{ ref('stg_facebook_ads') }} a
 left join {{ ref('stg_facebook_campaigns') }} c on a.campaign_id = c.campaign_id
 union all
 select 'snapchat' as platform, account_id, campaign_id, campaign_name
 from {{ ref('stg_snapchat_campaigns') }}
)
select {{ sk(['platform','account_id','campaign_id']) }} as campaign_key, * from campaigns

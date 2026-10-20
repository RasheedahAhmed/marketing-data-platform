with expected as (
 select 'facebook' as platform, upper(a.ad_currency_code) as currency_code, count(*) as n,
 sum(s.spend) as spend, sum(s.impressions) as impressions, sum(s.clicks) as clicks,
 count(s.impressions) as observed_impressions, count(s.clicks) as observed_clicks
 from {{ ref('stg_facebook_stats') }} s
 left join {{ ref('stg_facebook_accounts') }} a on s.account_id=a.account_id
 group by upper(a.ad_currency_code)
 union all
 select 'snapchat', currency_code, count(*), sum(spend), sum(impressions), sum(clicks), count(impressions), count(clicks)
 from {{ ref('stg_snapchat_stats') }} group by currency_code
), actual as (
 select platform, currency_code, count(*) as n, sum(spend) as spend,
 sum(impressions) as impressions, sum(clicks) as clicks,
 count(impressions) as observed_impressions, count(clicks) as observed_clicks
 from {{ ref('marketing_performance') }} group by platform,currency_code
)
select coalesce(e.platform,a.platform) as platform, coalesce(e.currency_code,a.currency_code) as currency_code
from expected e full outer join actual a on e.platform=a.platform and e.currency_code=a.currency_code
where e.n is null or a.n is null or e.n <> a.n or abs(e.spend-a.spend)>0.000001
 or coalesce(e.impressions,-1)<>coalesce(a.impressions,-1) or coalesce(e.clicks,-1)<>coalesce(a.clicks,-1)
 or e.observed_impressions<>a.observed_impressions or e.observed_clicks<>a.observed_clicks

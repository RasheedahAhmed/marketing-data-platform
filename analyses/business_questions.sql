-- Select catalog/schema first. Every monetary query groups by currency.
select platform, currency_code, min(date_day) as first_day, max(date_day) as last_day,
 sum(spend) as spend, sum(clicks) as known_clicks, sum(impressions) as known_impressions,
 sum(case when clicks is null then 1 else 0 end) as unknown_click_rows,
 sum(case when impressions is null then 1 else 0 end) as unknown_impression_rows
from {{ ref('marketing_performance') }} group by platform,currency_code;

-- Daily campaign trends; metrics already apply completeness rules.
select * from {{ ref('rpt_campaign_daily') }} order by date_day,platform,currency_code,campaign_id;

-- Campaign ranking by observed clicks, explicitly indicating incomplete inputs.
select platform, account_id, campaign_id, campaign_name, currency_code,
 sum(known_clicks) as known_clicks, sum(unknown_click_rows) as unknown_click_rows
from {{ ref('rpt_campaign_daily') }}
group by platform,account_id,campaign_id,campaign_name,currency_code
order by known_clicks desc;

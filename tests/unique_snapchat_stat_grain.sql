select ad_id, date_day, country_code, currency_code, count(*) as n from {{ ref('stg_snapchat_stats') }}
group by ad_id, date_day, country_code, currency_code having count(*) > 1

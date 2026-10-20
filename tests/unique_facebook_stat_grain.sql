select account_id, ad_id, date_day, count(*) as n from {{ ref('stg_facebook_stats') }}
group by account_id, ad_id, date_day having count(*) > 1

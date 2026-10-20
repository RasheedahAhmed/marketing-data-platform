select account_id,ad_id,count(*) as n from {{ ref('stg_facebook_ads') }} group by account_id,ad_id having count(*)>1

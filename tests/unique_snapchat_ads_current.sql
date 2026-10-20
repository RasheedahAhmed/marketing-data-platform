select ad_id,count(*) as n from {{ ref('stg_snapchat_ads') }} group by ad_id having count(*)>1

select ad_group_id,count(*) as n from {{ ref('stg_snapchat_adgroups') }} group by ad_group_id having count(*)>1

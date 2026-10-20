select ad_group_id,count(*) as n from {{ ref('stg_facebook_adgroups') }} group by ad_group_id having count(*)>1

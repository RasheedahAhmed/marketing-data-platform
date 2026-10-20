select campaign_id,count(*) as n from {{ ref('stg_facebook_campaigns') }} group by campaign_id having count(*)>1

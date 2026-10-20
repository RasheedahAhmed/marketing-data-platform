select a.ad_id, c.account_id, a.ad_group_id, g.campaign_id,
 a.ad_name, cast(null as string) as ad_status, g.ad_group_name, c.campaign_name,
 cast(null as string) as account_name,
 (g.ad_group_id is not null and c.campaign_id is not null) as hierarchy_complete
from {{ ref('stg_snapchat_ads') }} a
left join {{ ref('stg_snapchat_adgroups') }} g on a.ad_group_id = g.ad_group_id
left join {{ ref('stg_snapchat_campaigns') }} c on g.campaign_id = c.campaign_id

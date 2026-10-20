select a.ad_id, a.account_id, a.ad_group_id, a.campaign_id,
 a.ad_name, a.ad_status, g.ad_group_name, c.campaign_name,
 ac.account_name, upper(ac.ad_currency_code) as currency_code,
 (g.ad_group_id is not null and c.campaign_id is not null and ac.account_id is not null) as hierarchy_complete
from {{ ref('stg_facebook_ads') }} a
left join {{ ref('stg_facebook_adgroups') }} g on a.ad_group_id = g.ad_group_id
left join {{ ref('stg_facebook_campaigns') }} c on a.campaign_id = c.campaign_id
left join {{ ref('stg_facebook_accounts') }} ac on a.account_id = ac.account_id

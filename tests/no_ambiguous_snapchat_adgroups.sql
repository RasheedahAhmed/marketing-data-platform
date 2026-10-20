select ad_group_id, ad_group_updated_at, count(distinct _row_hash) as payloads
from {{ snapshot('snapchat_adgroups') }}
group by ad_group_id, ad_group_updated_at
having count(distinct _row_hash) > 1

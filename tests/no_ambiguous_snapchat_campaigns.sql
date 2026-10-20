select campaign_id, count(distinct _row_hash) as payloads
from {{ snapshot('snapchat_campaigns') }}
group by campaign_id
having count(distinct _row_hash) > 1

select campaign_id, campaign_updated_at, count(distinct _row_hash) as payloads
from {{ snapshot('facebook_campaigns') }}
group by campaign_id, campaign_updated_at
having count(distinct _row_hash) > 1

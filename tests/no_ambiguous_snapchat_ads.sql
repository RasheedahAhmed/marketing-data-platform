select ad_id, ad_detail_updated_at, count(distinct _row_hash) as payloads
from {{ snapshot('snapchat_ads') }}
group by ad_id, ad_detail_updated_at
having count(distinct _row_hash) > 1

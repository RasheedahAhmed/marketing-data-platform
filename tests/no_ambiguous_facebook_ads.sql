select account_id, ad_id, ad_updated_at, count(distinct _row_hash) as payloads
from {{ snapshot('facebook_ads') }}
group by account_id, ad_id, ad_updated_at
having count(distinct _row_hash) > 1

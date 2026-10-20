select account_id, account_updated_at, count(distinct _row_hash) as payloads
from {{ snapshot('facebook_accounts') }}
group by account_id, account_updated_at
having count(distinct _row_hash) > 1

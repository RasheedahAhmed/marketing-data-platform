with typed as (
 select distinct {{ clean('account_id') }} as account_id,
 {{ clean('account_name') }} as account_name,
 {{ clean('ad_currency_code') }} as ad_currency_code,
 try_cast({{ clean('account_updated_at') }} as timestamp) as updated_at,
 _row_hash
 from {{ snapshot('facebook_accounts') }}
), ranked as (
 select *, row_number() over (partition by account_id order by updated_at desc nulls last, _row_hash desc) as _rn
 from typed
)
select account_id, account_name, ad_currency_code, updated_at, _row_hash from ranked where _rn = 1

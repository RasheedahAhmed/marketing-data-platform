with typed as (
 select distinct {{ clean('ad_id') }} as ad_id,
 {{ clean('campaign_id') }} as campaign_id,
 {{ clean('ad_group_id') }} as ad_group_id,
 {{ clean('account_id') }} as account_id,
 {{ clean('ad_name') }} as ad_name,
 {{ clean('ad_status') }} as ad_status,
 try_cast({{ clean('ad_updated_at') }} as timestamp) as updated_at,
 _row_hash
 from {{ snapshot('facebook_ads') }}
), ranked as (
 select *, row_number() over (partition by account_id, ad_id order by updated_at desc nulls last, _row_hash desc) as _rn
 from typed
)
select ad_id, campaign_id, ad_group_id, account_id, ad_name, ad_status, updated_at, _row_hash from ranked where _rn = 1

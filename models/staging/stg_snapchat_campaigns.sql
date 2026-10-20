with typed as (
 select distinct {{ clean('campaign_id') }} as campaign_id,
 {{ clean('account_id') }} as account_id,
 {{ clean('campaign_name') }} as campaign_name,
 _row_hash
 from {{ snapshot('snapchat_campaigns') }}
), ranked as (
 select *, row_number() over (partition by campaign_id order by _row_hash desc) as _rn
 from typed
)
select campaign_id, account_id, campaign_name, _row_hash from ranked where _rn = 1

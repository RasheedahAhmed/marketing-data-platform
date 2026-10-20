with typed as (
 select distinct {{ clean('campaign_id') }} as campaign_id,
 {{ clean('campaign_name') }} as campaign_name,
 try_cast({{ clean('campaign_updated_at') }} as timestamp) as updated_at,
 _row_hash
 from {{ snapshot('facebook_campaigns') }}
), ranked as (
 select *, row_number() over (partition by campaign_id order by updated_at desc nulls last, _row_hash desc) as _rn
 from typed
)
select campaign_id, campaign_name, updated_at, _row_hash from ranked where _rn = 1

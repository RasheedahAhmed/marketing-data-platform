with typed as (
 select distinct {{ clean('ad_id') }} as ad_id,
 {{ clean('ad_group_id') }} as ad_group_id,
 {{ clean('ad_name') }} as ad_name,
 try_cast({{ clean('ad_detail_updated_at') }} as timestamp) as updated_at,
 _row_hash
 from {{ snapshot('snapchat_ads') }}
), ranked as (
 select *, row_number() over (partition by ad_id order by updated_at desc nulls last, _row_hash desc) as _rn
 from typed
)
select ad_id, ad_group_id, ad_name, updated_at, _row_hash from ranked where _rn = 1

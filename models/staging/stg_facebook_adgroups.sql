with typed as (
 select distinct {{ clean('ad_group_id') }} as ad_group_id,
 {{ clean('ad_group_name') }} as ad_group_name,
 try_cast({{ clean('ad_group_updated_at') }} as timestamp) as updated_at,
 _row_hash
 from {{ snapshot('facebook_adgroups') }}
), ranked as (
 select *, row_number() over (partition by ad_group_id order by updated_at desc nulls last, _row_hash desc) as _rn
 from typed
)
select ad_group_id, ad_group_name, updated_at, _row_hash from ranked where _rn = 1

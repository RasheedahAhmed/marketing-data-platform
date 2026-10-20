select distinct
    'facebook' as platform,
    {{ clean('ad_id') }} as ad_id,
    {{ clean('account_id') }} as account_id,
    try_cast({{ clean('ad_date') }} as date) as date_day,
    try_cast({{ clean('ad_spend') }} as decimal(20,6)) as spend,
    try_cast({{ clean('ad_impressions') }} as bigint) as impressions,
    try_cast({{ clean('ad_clicks') }} as bigint) as clicks,
    _batch_id,
    _row_hash
from {{ snapshot('facebook_stats') }}

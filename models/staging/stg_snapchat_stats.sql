select distinct
    'snapchat' as platform,
    {{ clean('ad_detail_id') }} as ad_id,
    upper({{ clean('ad_currency_code') }}) as currency_code,
    upper({{ clean('ad_country') }}) as country_code,
    {{ clean('data_src') }} as data_src,
    try_cast({{ clean('ad_date') }} as date) as date_day,
    try_cast({{ clean('ad_spend') }} as decimal(20,6)) as spend,
    try_cast({{ clean('ad_impressions') }} as bigint) as impressions,
    try_cast({{ clean('ad_clicks') }} as bigint) as clicks,
    _batch_id,
    _row_hash
from {{ snapshot('snapchat_stats') }}

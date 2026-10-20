select _row_hash from {{ snapshot('snapchat_stats') }}
where try_cast({{ clean('ad_date') }} as date) is null
 or try_cast({{ clean('ad_spend') }} as decimal(20,6)) is null
 or ({{ clean('ad_impressions') }} is not null and try_cast({{ clean('ad_impressions') }} as bigint) is null)
 or ({{ clean('ad_clicks') }} is not null and try_cast({{ clean('ad_clicks') }} as bigint) is null)

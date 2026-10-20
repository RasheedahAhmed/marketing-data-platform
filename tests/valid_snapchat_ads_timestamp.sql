select _row_hash from {{ snapshot('snapchat_ads') }} where try_cast({{ clean('ad_detail_updated_at') }} as timestamp) is null

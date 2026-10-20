select _row_hash from {{ snapshot('facebook_ads') }} where try_cast({{ clean('ad_updated_at') }} as timestamp) is null

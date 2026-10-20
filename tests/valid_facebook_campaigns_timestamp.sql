select _row_hash from {{ snapshot('facebook_campaigns') }} where try_cast({{ clean('campaign_updated_at') }} as timestamp) is null

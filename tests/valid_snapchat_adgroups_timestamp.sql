select _row_hash from {{ snapshot('snapchat_adgroups') }} where try_cast({{ clean('ad_group_updated_at') }} as timestamp) is null

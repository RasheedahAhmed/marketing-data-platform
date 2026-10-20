select _row_hash from {{ snapshot('facebook_accounts') }} where try_cast({{ clean('account_updated_at') }} as timestamp) is null

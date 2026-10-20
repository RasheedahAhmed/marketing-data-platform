select _row_hash from {{ ref('stg_snapchat_stats') }} where data_src <> 'snapchat_ads' or data_src is null

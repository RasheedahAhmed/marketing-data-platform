select account_id,count(*) as n from {{ ref('stg_facebook_accounts') }} group by account_id having count(*)>1

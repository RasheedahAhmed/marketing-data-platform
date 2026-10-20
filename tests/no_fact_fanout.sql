select 'row_count' as issue
where (select count(*) from {{ ref('marketing_performance') }}) <>
 ((select count(*) from {{ ref('stg_facebook_stats') }}) + (select count(*) from {{ ref('stg_snapchat_stats') }}))

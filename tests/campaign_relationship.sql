select f.performance_key from {{ ref('marketing_performance') }} f
left join {{ ref('dim_campaigns') }} d on f.campaign_key = d.campaign_key
where f.campaign_key is not null and d.campaign_key is null

select performance_key from {{ ref('marketing_performance') }}
where ((clicks is null or impressions is null or impressions=0) and ctr is not null)
 or ((clicks is null or clicks=0) and cpc is not null)
 or ((impressions is null or impressions=0) and cpm is not null)

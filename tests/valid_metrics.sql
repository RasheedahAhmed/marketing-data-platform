select performance_key from {{ ref('marketing_performance') }}
where spend is null or spend < 0 or impressions < 0 or clicks < 0
 or date_day is null or ad_id is null or currency_code is null
 or platform not in ('facebook','snapchat') or length(currency_code) <> 3

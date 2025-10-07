# Jinja2 Templates for Home Assistant Energy Management

## Overview

Jinja2 is the templating engine used throughout Home Assistant for creating dynamic values, conditions, and automations. For Australian energy management, Jinja2 templates enable sophisticated calculations for tariffs, solar optimization, and consumption analysis.

## Basic Jinja2 Syntax

### Variables and Filters
```jinja2
{# Comments - not rendered #}
{{ variable }}                    {# Output variable #}
{{ variable | filter }}           {# Apply filter #}
{{ variable | filter(arg) }}      {# Filter with argument #}
{% if condition %}...{% endif %}  {# Conditional logic #}
{% for item in list %}...{% endfor %}  {# Loops #}
```

### Common Filters for Energy Data
```jinja2
{{ value | float }}               {# Convert to number #}
{{ value | round(2) }}           {# Round to 2 decimal places #}
{{ value | abs }}                {# Absolute value #}
{{ value | max }}                {# Maximum value #}
{{ value | min }}                {# Minimum value #}
{{ value | sum }}                {# Sum of list #}
{{ timestamp | as_timestamp }}   {# Convert to Unix timestamp #}
```

## Australian Energy Calculations

### Time-of-Use Tariff Calculator
```jinja2
{# Dynamic electricity rate based on time and day #}
{% set hour = now().hour %}
{% set is_weekend = now().weekday() in [5, 6] %}
{% set is_summer = now().month in [12, 1, 2] %}

{% if is_weekend %}
  {% set rate = 0.18 %}  {# Weekend rate #}
{% elif is_summer and hour >= 14 and hour < 20 %}
  {% set rate = 0.45 %}  {# Summer peak (2-8pm) #}
{% elif hour >= 16 and hour < 20 %}
  {% set rate = 0.35 %}  {# Winter peak (4-8pm) #}
{% elif hour >= 7 and hour < 16 or hour >= 20 and hour < 22 %}
  {% set rate = 0.25 %}  {# Shoulder #}
{% else %}
  {% set rate = 0.16 %}  {# Off-peak #}
{% endif %}

{{ rate }}
```

### Solar Production Efficiency
```jinja2
{# Calculate solar system performance #}
{% set production = states('sensor.solar_production') | float %}
{% set capacity = 6.6 %}  {# kW system capacity #}
{% set irradiance = states('sensor.solar_irradiance') | float %}

{# Efficiency calculation #}
{% set expected = (capacity * irradiance / 1000) %}
{% set efficiency = (production / expected) * 100 if expected > 0 else 0 %}

{{ efficiency | round(1) }}%
```

### Battery Optimization Logic
```jinja2
{# Determine optimal battery action #}
{% set battery_soc = states('sensor.battery_soc') | float %}
{% set solar_excess = states('sensor.solar_excess') | float %}
{% set grid_price = states('sensor.electricity_rate') | float %}
{% set export_rate = states('sensor.feed_in_tariff') | float %}

{% if battery_soc < 20 %}
  {% set action = "charge_priority" %}
{% elif solar_excess > 2000 and battery_soc < 90 %}
  {% set action = "charge_from_solar" %}
{% elif grid_price > 0.30 and battery_soc > 50 %}
  {% set action = "discharge_to_house" %}
{% elif battery_soc > 95 and export_rate > 0.06 %}
  {% set action = "allow_export" %}
{% else %}
  {% set action = "standby" %}
{% endif %}

{{ action }}
```

## Advanced Energy Templates

### Demand Charge Calculator
```jinja2
{# Calculate 30-minute demand for demand charges #}
{% set power_readings = [] %}
{% for i in range(60) %}  {# 60 readings for 30 minutes at 30s intervals #}
  {% set timestamp = (now() - timedelta(seconds=i*30)) %}
  {% set reading = states.sensor.grid_import_power.history(timestamp, now()) %}
  {% if reading %}
    {% set power_readings = power_readings + [reading[0].state | float] %}
  {% endif %}
{% endfor %}

{# Average demand in kW #}
{% set avg_demand = (power_readings | sum / power_readings | length / 1000) if power_readings else 0 %}
{{ avg_demand | round(2) }}
```

### Cost Analysis Template
```jinja2
{# Daily cost breakdown #}
{% set start_of_day = now().replace(hour=0, minute=0, second=0, microsecond=0) %}
{% set grid_import = states('sensor.daily_grid_import') | float %}
{% set grid_export = states('sensor.daily_grid_export') | float %}

{# Get average rates for the day #}
{% set import_cost = grid_import * 0.25 %}  {# Average rate #}
{% set export_credit = grid_export * 0.05 %}  {# Feed-in tariff #}
{% set net_cost = import_cost - export_credit %}

{
  "import_cost": {{ import_cost | round(2) }},
  "export_credit": {{ export_credit | round(2) }},
  "net_cost": {{ net_cost | round(2) }},
  "self_consumption": {{ ((grid_import / (grid_import + grid_export)) * 100) | round(1) if (grid_import + grid_export) > 0 else 0 }}
}
```

### Grid Independence Calculator
```jinja2
{# Calculate energy independence percentage #}
{% set solar_production = states('sensor.daily_solar_production') | float %}
{% set grid_import = states('sensor.daily_grid_import') | float %}
{% set total_consumption = solar_production + grid_import %}

{% set independence = ((solar_production / total_consumption) * 100) if total_consumption > 0 else 0 %}
{{ independence | round(1) }}
```

## Seasonal Adjustments

### Summer vs Winter Optimization
```jinja2
{# Seasonal energy strategy #}
{% set month = now().month %}
{% set is_summer = month in [12, 1, 2] %}
{% set is_winter = month in [6, 7, 8] %}

{% if is_summer %}
  {# Summer: Focus on cooling efficiency #}
  {% set optimal_temp = 24 %}
  {% set peak_hours = [14, 15, 16, 17, 18, 19] %}
  {% set solar_weight = 1.2 %}  {# Longer days, more solar #}
{% elif is_winter %}
  {# Winter: Focus on heating efficiency #}
  {% set optimal_temp = 20 %}
  {% set peak_hours = [16, 17, 18, 19] %}
  {% set solar_weight = 0.8 %}  {# Shorter days, less solar #}
{% else %}
  {# Shoulder seasons #}
  {% set optimal_temp = 22 %}
  {% set peak_hours = [16, 17, 18, 19] %}
  {% set solar_weight = 1.0 %}
{% endif %}

{
  "optimal_temp": {{ optimal_temp }},
  "is_peak_hour": {{ now().hour in peak_hours }},
  "solar_factor": {{ solar_weight }}
}
```

### Weather-Adjusted Solar Forecast
```jinja2
{# Adjust solar forecast based on weather conditions #}
{% set base_forecast = 25 %}  {# kWh on clear day #}
{% set weather_condition = states('weather.home') %}
{% set cloud_cover = state_attr('weather.home', 'cloud_coverage') | float %}

{% if 'sunny' in weather_condition or 'clear' in weather_condition %}
  {% set weather_factor = 1.0 %}
{% elif 'partly' in weather_condition %}
  {% set weather_factor = 0.7 %}
{% elif 'cloudy' in weather_condition %}
  {% set weather_factor = 0.4 %}
{% elif 'rain' in weather_condition or 'storm' in weather_condition %}
  {% set weather_factor = 0.2 %}
{% else %}
  {% set weather_factor = 0.6 %}  {# Default for unknown conditions #}
{% endif %}

{# Apply cloud cover adjustment if available #}
{% if cloud_cover is not none %}
  {% set weather_factor = weather_factor * (1 - cloud_cover / 100) %}
{% endif %}

{{ (base_forecast * weather_factor) | round(1) }}
```

## Load Management Templates

### Appliance Priority Scoring
```jinja2
{# Priority scoring for load shedding #}
{% macro appliance_priority(appliance_name, current_time) %}
  {% set priorities = {
    'hot_water': 70,      # Can defer for hours
    'pool_pump': 60,      # Can defer for hours  
    'dishwasher': 50,     # Can defer until off-peak
    'washing_machine': 40, # Moderate priority
    'ev_charger': 30,     # Can use public charging
    'air_conditioning': 20, # Comfort priority
    'refrigerator': 10    # Essential - never shed
  } %}
  
  {% set base_priority = priorities.get(appliance_name, 50) %}
  
  {# Adjust for time of day #}
  {% set hour = current_time.hour %}
  {% if appliance_name == 'hot_water' and hour < 6 %}
    {% set base_priority = base_priority - 20 %}  {# Higher priority early morning #}
  {% elif appliance_name == 'air_conditioning' and (hour < 8 or hour > 22) %}
    {% set base_priority = base_priority + 20 %}  {# Lower priority outside comfort hours #}
  {% endif %}
  
  {{ base_priority }}
{% endmacro %}

{# Usage example #}
{{ appliance_priority('hot_water', now()) }}
```

### Dynamic Load Scheduling
```jinja2
{# Schedule loads based on solar forecast and pricing #}
{% set appliances = ['dishwasher', 'washing_machine', 'hot_water'] %}
{% set solar_forecast = [2, 8, 15, 20, 18, 12, 6, 2] %}  {# Hourly kW forecast #}
{% set pricing = [0.16, 0.16, 0.25, 0.35, 0.35, 0.25, 0.16, 0.16] %}  {# Hourly pricing #}

{% set schedule = {} %}
{% for appliance in appliances %}
  {% set power_req = {'dishwasher': 2, 'washing_machine': 1.5, 'hot_water': 3.6}[appliance] %}
  {% set duration = {'dishwasher': 2, 'washing_machine': 1, 'hot_water': 1}[appliance] %}
  
  {# Find best time slot #}
  {% set best_hour = 0 %}
  {% set best_score = 999 %}
  
  {% for hour in range(8) %}
    {% if solar_forecast[hour] >= power_req %}
      {# Can run on solar #}
      {% set score = 0 %}
    {% else %}
      {# Must use grid - factor in price #}
      {% set score = pricing[hour] * power_req %}
    {% endif %}
    
    {% if score < best_score %}
      {% set best_score = score %}
      {% set best_hour = hour %}
    {% endif %}
  {% endfor %}
  
  {% set schedule = schedule.update({appliance: {'hour': best_hour, 'score': best_score}}) %}
{% endfor %}

{{ schedule }}
```

## Error Handling and Validation

### Safe Number Conversion
```jinja2
{# Safely convert sensor values to numbers #}
{% macro safe_float(entity_id, default=0) %}
  {% set value = states(entity_id) %}
  {% if value not in ['unknown', 'unavailable', 'none', None] %}
    {% set num_value = value | float %}
    {% if num_value == num_value %}  {# Check for NaN #}
      {{ num_value }}
    {% else %}
      {{ default }}
    {% endif %}
  {% else %}
    {{ default }}
  {% endif %}
{% endmacro %}

{# Usage #}
{% set solar_power = safe_float('sensor.solar_production', 0) %}
{% set grid_power = safe_float('sensor.grid_import_power', 0) %}
```

### Data Validation Template
```jinja2
{# Validate energy readings for anomalies #}
{% macro validate_energy_reading(current, previous, max_change_percent=50) %}
  {% if previous == 0 %}
    {% set valid = true %}  {# First reading #}
  {% else %}
    {% set change_percent = ((current - previous) / previous * 100) | abs %}
    {% set valid = change_percent <= max_change_percent %}
  {% endif %}
  
  {
    "value": {{ current }},
    "valid": {{ valid | lower }},
    "change_percent": {{ change_percent | round(1) if previous != 0 else 0 }}
  }
{% endmacro %}

{# Usage #}
{{ validate_energy_reading(
  states('sensor.solar_production') | float,
  states('sensor.solar_production_previous') | float
) }}
```

## Testing and Debugging Templates

### Template Testing in Developer Tools
```jinja2
{# Use this in Developer Tools > Template to test #}
{% set test_data = {
  'solar_production': 4500,
  'grid_import': 1200,
  'battery_soc': 65,
  'electricity_rate': 0.28
} %}

{# Test your template logic with known values #}
{% set excess_solar = test_data.solar_production - test_data.grid_import %}
{% if excess_solar > 2000 and test_data.battery_soc < 90 %}
  Charge battery from excess solar
{% elif test_data.electricity_rate > 0.30 and test_data.battery_soc > 50 %}
  Discharge battery to house
{% else %}
  Maintain current state
{% endif %}
```

### Debug Output Template
```jinja2
{# Add debug information to templates #}
{% set debug_mode = states('input_boolean.template_debug') == 'on' %}
{% set calculation_result = (states('sensor.solar_production') | float) / 1000 %}

{% if debug_mode %}
{# Debug output #}
Debug Info:
- Solar Production: {{ states('sensor.solar_production') }}
- Converted: {{ calculation_result }}
- Timestamp: {{ now() }}
{% endif %}

{# Return actual result #}
{{ calculation_result | round(2) }}
```

## Jerry's Jinja2 Best Practices

### 1. Performance Optimization
- **Minimize state lookups**: Store `states()` calls in variables
- **Use macros**: Reuse common calculations
- **Avoid complex loops**: Pre-calculate where possible
- **Cache results**: Use template sensors for expensive calculations

### 2. Readability and Maintenance
- **Add comments**: Explain complex logic
- **Use meaningful variable names**: Clear intent
- **Break down complex templates**: Use multiple simpler templates
- **Document units**: Always specify kW, kWh, W, etc.

### 3. Error Resilience
- **Handle unknown states**: Always check for 'unknown'/'unavailable'
- **Provide defaults**: Use fallback values
- **Validate inputs**: Check for reasonable ranges
- **Test edge cases**: Consider startup conditions and sensor failures

### 4. Australian Energy Considerations
- **Time zones**: Account for AEST/AEDT changes
- **Seasonal variations**: Adjust for Australian seasons
- **Public holidays**: Consider impact on tariffs
- **Network events**: Handle grid disconnection scenarios
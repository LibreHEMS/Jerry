# Amber Electric Integration Guide

## Overview

Amber Electric is Australia's first electricity retailer to offer real-time wholesale electricity pricing to residential customers. By exposing the actual cost of electricity throughout the day, Amber enables sophisticated energy management and significant cost savings for smart energy users.

## How Amber Electric Works

### Wholesale Pricing Model
- **Real-time pricing**: Electricity prices change every 30 minutes based on National Electricity Market (NEM) wholesale prices
- **Transparent pricing**: No markup on wholesale prices - just a subscription fee
- **SmartShift™**: Automated device control to avoid high-price periods
- **Price forecasts**: 24-48 hour price predictions for planning

### Australian Market Integration
- **NEM connectivity**: Direct integration with AEMO pricing data
- **Regional pricing**: Different prices for NSW, VIC, QLD, SA, TAS
- **Network charges**: Includes distribution network service provider (DNSP) charges
- **Green energy**: Optional renewable energy certificates

## Amber Electric API Integration

### API Authentication
```python
# Amber Electric API setup
import requests
from datetime import datetime, timedelta

class AmberElectricAPI:
    def __init__(self, api_token, site_id):
        self.api_token = api_token
        self.site_id = site_id
        self.base_url = "https://api.amber.com.au/v1"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
    
    def get_current_prices(self):
        """Get current electricity prices"""
        url = f"{self.base_url}/sites/{self.site_id}/prices/current"
        response = requests.get(url, headers=self.headers)
        return response.json()
    
    def get_price_forecast(self, hours=24):
        """Get price forecast for next N hours"""
        end_time = datetime.now() + timedelta(hours=hours)
        url = f"{self.base_url}/sites/{self.site_id}/prices"
        params = {
            "startDate": datetime.now().isoformat(),
            "endDate": end_time.isoformat()
        }
        response = requests.get(url, headers=self.headers, params=params)
        return response.json()
```

### Home Assistant Integration
```yaml
# configuration.yaml
rest:
  - resource: "https://api.amber.com.au/v1/sites/YOUR_SITE_ID/prices/current"
    headers:
      Authorization: "Bearer YOUR_API_TOKEN"
    scan_interval: 300  # 5 minutes
    sensor:
      - name: "Amber Import Price"
        value_template: "{{ value_json[0].perKwh }}"
        unit_of_measurement: "AUD/kWh"
        device_class: monetary
        
      - name: "Amber Export Price"
        value_template: "{{ value_json[1].perKwh if value_json|length > 1 else 0 }}"
        unit_of_measurement: "AUD/kWh"
        device_class: monetary
        
      - name: "Amber Price Spike"
        value_template: "{{ value_json[0].spike }}"
        
      - name: "Amber Renewables Percentage"
        value_template: "{{ value_json[0].renewables }}"
        unit_of_measurement: "%"

  # Price forecast (next 24 hours)
  - resource: "https://api.amber.com.au/v1/sites/YOUR_SITE_ID/prices"
    headers:
      Authorization: "Bearer YOUR_API_TOKEN"
    scan_interval: 3600  # 1 hour
    sensor:
      - name: "Amber Price Forecast"
        value_template: "{{ value_json | length }}"
        json_attributes:
          - "forecast_data"
        json_attributes_path: "$"
```

## Smart Energy Automations with Amber

### Spike Period Protection
```yaml
# Automatically reduce load during price spikes
automation:
  - alias: "Amber Price Spike Response"
    trigger:
      - platform: state
        entity_id: sensor.amber_price_spike
        to: "true"
    action:
      # Turn off non-essential loads
      - service: switch.turn_off
        entity_id:
          - switch.pool_pump
          - switch.hot_water_boost
          - switch.ev_charger
      
      # Reduce air conditioning
      - service: climate.set_temperature
        entity_id: climate.ducted_system
        data:
          temperature: >
            {% if states('climate.ducted_system') == 'heat' %}
              {{ state_attr('climate.ducted_system', 'temperature') - 2 }}
            {% else %}
              {{ state_attr('climate.ducted_system', 'temperature') + 2 }}
            {% endif %}
      
      # Notify users
      - service: notify.mobile_app
        data:
          message: "Amber price spike detected! Reducing load automatically."
          title: "High Electricity Prices"
```

### Negative Pricing Opportunities
```yaml
# Take advantage of negative pricing (paid to use electricity)
automation:
  - alias: "Amber Negative Pricing"
    trigger:
      - platform: numeric_state
        entity_id: sensor.amber_import_price
        below: 0  # Negative pricing
    condition:
      - condition: numeric_state
        entity_id: sensor.battery_soc
        below: 95  # Battery not full
    action:
      # Charge battery from grid
      - service: switch.turn_on
        entity_id: switch.battery_charge_from_grid
      
      # Turn on energy-intensive appliances
      - service: switch.turn_on
        entity_id:
          - switch.hot_water_boost
          - switch.pool_pump
      
      # Pre-cool/heat house
      - service: climate.set_temperature
        entity_id: climate.ducted_system
        data:
          temperature: >
            {% set season = "summer" if now().month in [12, 1, 2] else "winter" %}
            {% if season == "summer" %}
              20  # Pre-cool in summer
            {% else %}
              24  # Pre-heat in winter
            {% endif %}
```

### Optimal EV Charging
```yaml
# Schedule EV charging for lowest prices
automation:
  - alias: "Amber Optimal EV Charging"
    trigger:
      - platform: state
        entity_id: device_tracker.tesla_model_3
        to: "home"
    condition:
      - condition: numeric_state
        entity_id: sensor.ev_battery_level
        below: 80
    action:
      # Wait for optimal pricing
      - wait_template: >
          {% set current_price = states('sensor.amber_import_price') | float %}
          {% set forecast = state_attr('sensor.amber_price_forecast', 'forecast_data') %}
          {% set next_4_hours = forecast[:8] if forecast else [] %}  # 8 x 30min periods
          {% set min_price = next_4_hours | map(attribute='perKwh') | min if next_4_hours else current_price %}
          {{ current_price <= min_price * 1.1 }}  # Within 10% of minimum
        timeout: "04:00:00"  # Maximum 4 hour wait
        
      - service: switch.turn_on
        entity_id: switch.ev_charger
```

### Solar Export Optimization
```yaml
# Optimize solar export timing with Amber rates
automation:
  - alias: "Amber Solar Export Strategy"
    trigger:
      - platform: numeric_state
        entity_id: sensor.solar_production
        above: 3000  # 3kW excess solar
    action:
      - choose:
          # High export prices - export immediately
          - conditions:
              - condition: numeric_state
                entity_id: sensor.amber_export_price
                above: 0.08  # 8c/kWh
            sequence:
              - service: number.set_value
                entity_id: number.battery_export_limit
                data:
                  value: 5000  # Maximum export
                  
          # Low export prices - store in battery first
          - conditions:
              - condition: numeric_state
                entity_id: sensor.amber_export_price
                below: 0.03  # 3c/kWh
              - condition: numeric_state
                entity_id: sensor.battery_soc
                below: 90
            sequence:
              - service: number.set_value
                entity_id: number.battery_charge_rate
                data:
                  value: 5000  # Charge battery first
        
        # Default - balanced approach
        default:
          - service: number.set_value
            entity_id: number.battery_charge_rate
            data:
              value: 2500  # Moderate battery charging
```

## Advanced Amber Strategies

### Price Forecasting with Machine Learning
```python
# Predict price patterns for better automation
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import numpy as np

class AmberPricePredictor:
    def __init__(self, api):
        self.api = api
        self.model = RandomForestRegressor(n_estimators=100)
        
    def prepare_features(self, timestamp):
        """Create features for price prediction"""
        return {
            'hour': timestamp.hour,
            'day_of_week': timestamp.weekday(),
            'month': timestamp.month,
            'is_weekend': timestamp.weekday() >= 5,
            'season': self.get_season(timestamp.month)
        }
    
    def get_season(self, month):
        """Australian seasons"""
        if month in [12, 1, 2]:
            return 'summer'
        elif month in [3, 4, 5]:
            return 'autumn'
        elif month in [6, 7, 8]:
            return 'winter'
        else:
            return 'spring'
    
    def predict_price_trend(self, hours_ahead=24):
        """Predict if prices will be higher or lower"""
        current_price = self.api.get_current_prices()[0]['perKwh']
        forecast = self.api.get_price_forecast(hours_ahead)
        
        future_prices = [p['perKwh'] for p in forecast]
        avg_future_price = np.mean(future_prices)
        
        return {
            'current_price': current_price,
            'forecast_avg': avg_future_price,
            'trend': 'up' if avg_future_price > current_price else 'down',
            'confidence': abs(avg_future_price - current_price) / current_price
        }
```

### Dynamic Load Scheduling
```yaml
# Template for dynamic appliance scheduling
template:
  - sensor:
      - name: "Amber Optimal Schedule"
        state: "{{ states('sensor.amber_price_forecast') }}"
        attributes:
          hot_water_start: >
            {% set forecast = state_attr('sensor.amber_price_forecast', 'forecast_data') %}
            {% if forecast %}
              {% set prices_with_time = [] %}
              {% for period in forecast[:48] %}  # Next 24 hours
                {% set prices_with_time = prices_with_time + [(period.perKwh, period.nemTime)] %}
              {% endfor %}
              {% set sorted_prices = prices_with_time | sort %}
              {{ sorted_prices[0][1] }}  # Time of cheapest period
            {% else %}
              "22:00"  # Default off-peak
            {% endif %}
            
          pool_pump_schedule: >
            {% set forecast = state_attr('sensor.amber_price_forecast', 'forecast_data') %}
            {% if forecast %}
              {% set cheap_periods = [] %}
              {% for period in forecast[:48] %}
                {% if period.perKwh < 0.15 %}  # Cheap threshold
                  {% set cheap_periods = cheap_periods + [period.nemTime] %}
                {% endif %}
              {% endfor %}
              {{ cheap_periods[:6] }}  # Best 6 periods (3 hours)
            {% else %}
              ["22:00", "22:30", "23:00", "23:30", "00:00", "00:30"]
            {% endif %}
```

### Cost Tracking and Analytics
```yaml
# Track daily costs and savings with Amber
template:
  - sensor:
      - name: "Daily Amber Cost"
        unit_of_measurement: "AUD"
        state: >
          {% set import_kwh = states('sensor.daily_grid_import') | float %}
          {% set export_kwh = states('sensor.daily_grid_export') | float %}
          {% set avg_import_price = states('sensor.avg_amber_import_price_today') | float %}
          {% set avg_export_price = states('sensor.avg_amber_export_price_today') | float %}
          
          {% set import_cost = import_kwh * avg_import_price %}
          {% set export_credit = export_kwh * avg_export_price %}
          {{ (import_cost - export_credit) | round(2) }}
          
      - name: "Amber vs Fixed Rate Savings"
        unit_of_measurement: "AUD"
        state: >
          {% set amber_cost = states('sensor.daily_amber_cost') | float %}
          {% set total_kwh = states('sensor.daily_grid_import') | float %}
          {% set fixed_rate = 0.28 %}  # Typical fixed rate
          {% set fixed_cost = total_kwh * fixed_rate %}
          {{ (fixed_cost - amber_cost) | round(2) }}
```

## Amber SmartShift™ Integration

### API Control of Appliances
```python
# SmartShift device control via Amber API
class AmberSmartShift:
    def __init__(self, api_token, site_id):
        self.api = AmberElectricAPI(api_token, site_id)
        
    def register_device(self, device_id, device_type, power_rating):
        """Register a device for SmartShift control"""
        url = f"{self.api.base_url}/sites/{self.api.site_id}/devices"
        data = {
            "deviceId": device_id,
            "type": device_type,  # "hot_water", "pool_pump", "ev_charger"
            "powerRating": power_rating,
            "controllable": True
        }
        response = requests.post(url, headers=self.api.headers, json=data)
        return response.json()
    
    def set_device_preferences(self, device_id, preferences):
        """Set device control preferences"""
        url = f"{self.api.base_url}/sites/{self.api.site_id}/devices/{device_id}/preferences"
        response = requests.put(url, headers=self.api.headers, json=preferences)
        return response.json()
```

### Home Assistant SmartShift Integration
```yaml
# Integrate with Amber's SmartShift recommendations
rest_command:
  amber_smartshift_update:
    url: "https://api.amber.com.au/v1/sites/{{ site_id }}/smartshift"
    method: POST
    headers:
      Authorization: "Bearer {{ api_token }}"
    payload: >
      {
        "devices": [
          {
            "deviceId": "hot_water_system",
            "currentState": "{{ states('switch.hot_water') }}",
            "powerConsumption": {{ states('sensor.hot_water_power') | float }}
          },
          {
            "deviceId": "pool_pump",
            "currentState": "{{ states('switch.pool_pump') }}",
            "powerConsumption": {{ states('sensor.pool_pump_power') | float }}
          }
        ]
      }

# Automation to follow SmartShift recommendations
automation:
  - alias: "Follow Amber SmartShift"
    trigger:
      - platform: state
        entity_id: sensor.amber_smartshift_recommendation
    action:
      - service: >
          {% set recommendation = states('sensor.amber_smartshift_recommendation') %}
          {% if recommendation == 'reduce_load' %}
            script.amber_reduce_load
          {% elif recommendation == 'increase_load' %}
            script.amber_increase_load
          {% endif %}
```

## Monitoring and Notifications

### Price Alert System
```yaml
# Alert for price changes
automation:
  - alias: "Amber Price Alerts"
    trigger:
      # High price alert
      - platform: numeric_state
        entity_id: sensor.amber_import_price
        above: 0.50  # 50c/kWh
      # Negative pricing alert
      - platform: numeric_state
        entity_id: sensor.amber_import_price
        below: 0
    action:
      - service: notify.mobile_app
        data:
          title: "Amber Price Alert"
          message: >
            {% if trigger.above %}
              High electricity price: ${{ states('sensor.amber_import_price') }}/kWh
              Spike period: {{ states('sensor.amber_price_spike') }}
            {% else %}
              Negative pricing! Get paid to use electricity: ${{ states('sensor.amber_import_price') }}/kWh
            {% endif %}
          data:
            actions:
              - action: "reduce_load"
                title: "Reduce Load"
              - action: "view_forecast"
                title: "View Forecast"
```

### Daily Cost Reporting
```yaml
# Daily cost and usage summary
automation:
  - alias: "Daily Amber Summary"
    trigger:
      - platform: time
        at: "23:55:00"
    action:
      - service: notify.mobile_app
        data:
          title: "Daily Amber Summary"
          message: >
            Today's electricity cost: ${{ states('sensor.daily_amber_cost') }}
            Vs fixed rate: ${{ states('sensor.amber_vs_fixed_rate_savings') }} saved
            
            Usage:
            - Import: {{ states('sensor.daily_grid_import') }}kWh
            - Export: {{ states('sensor.daily_grid_export') }}kWh
            - Solar: {{ states('sensor.daily_solar_production') }}kWh
            
            Avg prices:
            - Import: ${{ states('sensor.avg_amber_import_price_today') }}/kWh
            - Export: ${{ states('sensor.avg_amber_export_price_today') }}/kWh
```

## Jerry's Amber Electric Recommendations

### Getting Started with Amber
1. **Assess suitability**: Best for homes with solar, batteries, or flexible loads
2. **Install monitoring**: Smart meter and real-time usage tracking essential
3. **Start with automation**: Begin with simple spike period protection
4. **Gradual optimization**: Add more sophisticated automations over time

### Maximizing Amber Benefits
1. **Load flexibility**: The more loads you can shift, the greater the savings
2. **Battery storage**: Essential for arbitrage opportunities
3. **Smart appliances**: Automated control provides best results
4. **Understanding patterns**: Learn your local price patterns and grid events

### Risk Management
1. **Set limits**: Maximum daily/monthly spend limits
2. **Backup strategies**: Alternative heating/cooling during extended high prices
3. **Monitor closely**: Check bills and usage patterns regularly
4. **Emergency overrides**: Manual control when automation fails

### Common Amber Scenarios for Australian Homes
1. **Solar + Battery**: Store cheap electricity, avoid expensive periods
2. **EV Charging**: Charge during negative pricing, avoid peak costs
3. **Pool Heating**: Run during surplus renewable periods
4. **Hot Water**: Shift heating to cheapest periods
5. **Air Conditioning**: Pre-cool/heat before expensive periods
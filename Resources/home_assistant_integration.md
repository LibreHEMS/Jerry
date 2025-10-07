# Home Assistant Integration Guide

## Overview

Home Assistant is an open-source home automation platform that puts local control and privacy first. For Australian homeowners, it provides comprehensive energy management, solar monitoring, and smart home automation capabilities.

## Core Components for Energy Management

### 1. Energy Dashboard
Built-in energy monitoring with support for:
- **Solar production tracking**
- **Grid import/export monitoring** 
- **Individual device consumption**
- **Battery state of charge**
- **Cost tracking with dynamic pricing**

### 2. Integration Ecosystem
Over 2000 integrations including:
- **Solar inverters**: Fronius, SolarEdge, Enphase, SMA
- **Smart meters**: Various Australian DNSP meters
- **Battery systems**: Tesla Powerwall, Enphase, LG Chem
- **EV chargers**: Tesla, Zappi, EVSE Australia

## Australian Energy Integrations

### Solar Inverter Integration

#### Fronius Integration
```yaml
# configuration.yaml
fronius:
  - resource: "http://192.168.1.100"  # Inverter IP
    scan_interval: 10  # seconds
    monitored_conditions:
      - "sensor.power_photovoltaics"
      - "sensor.energy_day"
      - "sensor.energy_total"
```

#### SolarEdge Integration
```yaml
# configuration.yaml
solaredge:
  api_key: "your_api_key"
  site_id: "12345"
  name: "Home Solar"
```

#### Enphase Envoy Integration
```yaml
# configuration.yaml
enphase_envoy:
  host: "192.168.1.101"  # Envoy IP
  username: "envoy"
  password: "last_6_of_serial"
```

### Smart Meter Integration

#### Modbus TCP (Common for Australian meters)
```yaml
# configuration.yaml
modbus:
  - name: "Smart Meter"
    type: tcp
    host: 192.168.1.102
    port: 502
    sensors:
      - name: "Grid Import Energy"
        address: 0
        unit_of_measurement: "kWh"
        device_class: energy
        state_class: total_increasing
        
      - name: "Grid Export Energy"
        address: 2
        unit_of_measurement: "kWh"
        device_class: energy
        state_class: total_increasing
        
      - name: "Grid Import Power"
        address: 4
        unit_of_measurement: "W"
        device_class: power
        state_class: measurement
```

#### REST API Integration (Some retailers)
```yaml
# configuration.yaml
rest:
  - resource: "https://api.retailer.com.au/usage"
    headers:
      Authorization: "Bearer YOUR_TOKEN"
    scan_interval: 300  # 5 minutes
    sensor:
      - name: "Daily Usage"
        value_template: "{{ value_json.daily_usage }}"
        unit_of_measurement: "kWh"
```

### Battery System Integration

#### Tesla Powerwall
```yaml
# configuration.yaml
powerwall:
  ip_address: "192.168.1.103"
  password: "your_password"
```

#### Generic Battery via Modbus
```yaml
# configuration.yaml
modbus:
  - name: "Battery System"
    type: tcp
    host: 192.168.1.104
    port: 502
    sensors:
      - name: "Battery SOC"
        address: 0
        unit_of_measurement: "%"
        device_class: battery
        
      - name: "Battery Power"
        address: 2
        unit_of_measurement: "W"
        device_class: power
```

## Energy Automations

### Peak Demand Management
```yaml
# automations.yaml
- alias: "Peak Demand Control"
  trigger:
    - platform: numeric_state
      entity_id: sensor.grid_import_power
      above: 8000  # 8kW threshold
  action:
    - service: switch.turn_off
      entity_id: switch.pool_pump
    - service: climate.set_temperature
      entity_id: climate.ducted_heating
      data:
        temperature: 20  # Reduce by 2 degrees
    - service: notify.mobile_app
      data:
        message: "Peak demand detected - reducing load"
```

### Solar Export Optimization
```yaml
- alias: "Maximize Solar Export"
  trigger:
    - platform: numeric_state
      entity_id: sensor.solar_production
      above: 5000  # 5kW excess solar
  condition:
    - condition: numeric_state
      entity_id: sensor.battery_soc
      above: 90  # Battery nearly full
  action:
    - service: switch.turn_on
      entity_id: switch.hot_water_boost
    - service: climate.set_temperature
      entity_id: climate.ducted_heating
      data:
        temperature: 24  # Pre-heat with solar
```

### Time-Based Load Shifting
```yaml
- alias: "Off-Peak Hot Water"
  trigger:
    - platform: time
      at: "22:00:00"  # Off-peak starts
  condition:
    - condition: numeric_state
      entity_id: sensor.hot_water_temperature
      below: 55  # Needs heating
  action:
    - service: switch.turn_on
      entity_id: switch.hot_water_element
```

### EV Charging Optimization
```yaml
- alias: "Smart EV Charging"
  trigger:
    - platform: state
      entity_id: device_tracker.tesla_model_3
      to: "home"
  condition:
    - condition: numeric_state
      entity_id: sensor.ev_battery_level
      below: 80
  action:
    - choose:
        # Solar available - charge immediately
        - conditions:
            - condition: numeric_state
              entity_id: sensor.solar_production
              above: 3000  # 3kW+ solar
        - service: switch.turn_on
          entity_id: switch.ev_charger
      # Default - charge during off-peak
      default:
        - wait_for_trigger:
            - platform: time
              at: "22:00:00"  # Off-peak
        - service: switch.turn_on
          entity_id: switch.ev_charger
```

## Australian Specific Configurations

### Electricity Tariff Templates
```yaml
# Time-of-Use Tariff (Common in Australia)
template:
  - sensor:
      - name: "Current Electricity Rate"
        unit_of_measurement: "AUD/kWh"
        state: >
          {% set hour = now().hour %}
          {% set is_weekend = now().weekday() in [5, 6] %}
          {% if is_weekend %}
            0.18  # Weekend rate
          {% elif hour >= 16 and hour < 20 %}
            0.35  # Peak (4-8pm weekdays)
          {% elif hour >= 7 and hour < 16 or hour >= 20 and hour < 22 %}
            0.25  # Shoulder
          {% else %}
            0.16  # Off-peak
          {% endif %}

  - sensor:
      - name: "Feed-in Tariff Rate"
        unit_of_measurement: "AUD/kWh"
        state: >
          {% if now().hour >= 10 and now().hour < 15 %}
            0.07  # Higher midday rate (some retailers)
          {% else %}
            0.05  # Standard FiT
          {% endif %}
```

### Demand Charge Monitoring
```yaml
# Track 30-minute demand (common in Australia)
template:
  - sensor:
      - name: "30min Demand Average"
        unit_of_measurement: "kW"
        state: >
          {{ states('sensor.grid_import_power') | float / 1000 }}
        attributes:
          rolling_30min_max: >
            {% set values = state_attr('sensor.30min_demand_average', 'values') or [] %}
            {% set current = states('sensor.grid_import_power') | float / 1000 %}
            {% set new_values = (values + [current])[-60:] %}  # 30min at 30s intervals
            {{ new_values | max }}
```

### Network Export Limiting
```yaml
# Limit solar export to comply with network rules
automation:
  - alias: "Export Limiting"
    trigger:
      - platform: numeric_state
        entity_id: sensor.solar_export_power
        above: 5000  # 5kW network limit
    action:
      - service: number.set_value
        entity_id: number.inverter_export_limit
        data:
          value: 5000  # Curtail to network limit
```

## Dashboard Configuration

### Energy Overview Dashboard
```yaml
# dashboard configuration
type: energy
title: "Home Energy"
cards:
  - type: energy-usage-graph
    title: "Energy Usage"
  - type: energy-solar-graph
    title: "Solar Production"
  - type: energy-grid-neutrality-gauge
    title: "Grid Independence"
  - type: energy-carbon-consumed-gauge
    title: "Carbon Footprint"
```

### Custom Energy Cards
```yaml
# Lovelace dashboard card
type: vertical-stack
cards:
  - type: horizontal-stack
    cards:
      - type: entity
        entity: sensor.solar_production
        name: "Solar Now"
        icon: mdi:solar-power
      - type: entity
        entity: sensor.grid_import_power
        name: "Grid Usage"
        icon: mdi:transmission-tower
      - type: entity
        entity: sensor.battery_soc
        name: "Battery"
        icon: mdi:battery
        
  - type: energy-flow-card
    entities:
      grid_consumption: sensor.grid_import_power
      grid_production: sensor.grid_export_power
      solar_production: sensor.solar_production
      battery_consumption: sensor.battery_discharge_power
      battery_production: sensor.battery_charge_power
```

## Advanced Integrations

### Weather-Based Predictions
```yaml
# Solar forecasting based on weather
template:
  - sensor:
      - name: "Solar Forecast Today"
        unit_of_measurement: "kWh"
        state: >
          {% set cloud_cover = states('weather.home') %}
          {% set base_production = 30 %}  # kWh on clear day
          {% if 'sunny' in cloud_cover %}
            {{ base_production }}
          {% elif 'partly' in cloud_cover %}
            {{ base_production * 0.7 }}
          {% elif 'cloudy' in cloud_cover %}
            {{ base_production * 0.3 }}
          {% else %}
            {{ base_production * 0.1 }}
          {% endif %}
```

### Grid Services Integration
```yaml
# Virtual Power Plant participation
automation:
  - alias: "VPP Demand Response"
    trigger:
      - platform: state
        entity_id: binary_sensor.vpp_event
        to: "on"
    action:
      - service: switch.turn_off
        entity_id: 
          - switch.pool_pump
          - switch.hot_water
      - service: climate.set_temperature
        entity_id: climate.ducted_heating
        data:
          temperature: 18  # Reduce during demand response
```

### Energy Market Integration
```yaml
# NEM price tracking (example)
rest:
  - resource: "https://api.nemosis.com.au/v1/spot-price"
    scan_interval: 300
    sensor:
      - name: "NEM Spot Price"
        value_template: "{{ value_json.price }}"
        unit_of_measurement: "AUD/MWh"
```

## Troubleshooting

### Common Issues

#### 1. Inverter Communication Problems
- **Check network connectivity**: Ping inverter IP address
- **Verify credentials**: Some inverters require authentication
- **Update firmware**: Ensure latest inverter firmware
- **Network isolation**: Some networks isolate IoT devices

#### 2. Inaccurate Energy Readings
- **Sensor calibration**: Compare with meter readings
- **Unit conversion**: Ensure W/kW consistency
- **Time synchronization**: Check device time settings
- **Modbus configuration**: Verify register addresses

#### 3. Automation Not Triggering
- **State conditions**: Check entity state history
- **Template syntax**: Test templates in Developer Tools
- **Time zones**: Ensure correct timezone configuration
- **Entity availability**: Check if sensors are available

### Debugging Tools
```yaml
# Enable detailed logging
logger:
  default: info
  logs:
    homeassistant.components.modbus: debug
    homeassistant.components.fronius: debug
    homeassistant.components.automation: debug
```

## Jerry's Home Assistant Recommendations

### Essential Add-ons for Australian Homes
1. **EMHASS**: Energy optimization
2. **InfluxDB**: Long-term data storage
3. **Grafana**: Advanced visualization
4. **Node-RED**: Visual automation programming
5. **Mosquitto**: MQTT broker for IoT devices

### Configuration Best Practices
1. **Backup regularly**: Use snapshots and cloud backups
2. **Document changes**: Comment your configurations
3. **Test automations**: Use safe modes and rollback plans
4. **Monitor performance**: Watch system resources
5. **Security**: Use HTTPS, strong passwords, VPN access

### Performance Optimization
1. **Database maintenance**: Regular purging of old data
2. **Sensor filtering**: Only record necessary state changes
3. **Automation efficiency**: Minimize complex templates
4. **Network optimization**: Wired connections for critical devices
5. **Hardware sizing**: Adequate compute resources for your setup
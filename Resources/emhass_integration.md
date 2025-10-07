# EMHASS (Energy Management for Home Assistant) Integration

## Overview

EMHASS (Energy Management for Home Assistant) is an open-source energy management system that optimizes home energy usage based on dynamic electricity pricing, renewable energy production, and household consumption patterns.

## Key Features

### 1. Dynamic Energy Optimization
- **Real-time pricing integration**: Works with variable electricity tariffs
- **Solar production forecasting**: Uses weather data to predict PV generation
- **Load scheduling**: Optimizes high-energy appliances based on grid conditions
- **Battery management**: Intelligent charge/discharge cycles for home batteries

### 2. Home Assistant Integration
- **Seamless integration**: Native Home Assistant add-on
- **Sensor integration**: Reads from smart meters, inverters, and IoT devices
- **Automation triggers**: Creates automations based on optimization results
- **Dashboard visualization**: Custom Lovelace cards for energy insights

### 3. Machine Learning Optimization
- **Linear programming**: Uses optimization algorithms for decision making
- **Historical data analysis**: Learns from past consumption patterns
- **Weather-based forecasting**: Integrates meteorological data for predictions
- **Multi-objective optimization**: Balances cost, emissions, and comfort

## Australian Implementation

### Electricity Market Integration
```yaml
# EMHASS configuration for Australian NEM
nem_zone: "NSW1"  # or VIC1, QLD1, SA1, TAS1
tariff_structure:
  - peak_hours: "16:00-20:00"
    peak_rate: 0.32  # $/kWh
  - shoulder_hours: "07:00-16:00,20:00-22:00"
    shoulder_rate: 0.24  # $/kWh
  - off_peak_hours: "22:00-07:00"
    off_peak_rate: 0.16  # $/kWh

feed_in_tariff:
  rate: 0.05  # $/kWh exported
  time_periods: "all"  # or specific time ranges
```

### Solar and Battery Configuration
```yaml
pv_system:
  capacity_kw: 6.6
  orientation: 0  # North-facing
  tilt: 25        # Optimal for Australian latitudes
  efficiency: 0.85
  inverter_efficiency: 0.95

battery_system:
  capacity_kwh: 13.5  # Tesla Powerwall 2 example
  max_charge_rate: 5.0  # kW
  max_discharge_rate: 5.0  # kW
  round_trip_efficiency: 0.90
  min_soc: 0.10  # Minimum state of charge
  max_soc: 0.95  # Maximum state of charge
```

## Jerry's EMHASS Expertise

### Configuration Guidance
Jerry can help Australian homeowners with:

1. **System Sizing**
   - Solar panel capacity recommendations
   - Battery storage sizing based on usage patterns
   - Inverter selection for optimal performance

2. **Tariff Optimization**
   - Time-of-use tariff analysis
   - Feed-in tariff maximization strategies
   - Retailer comparison and switching advice

3. **Load Management**
   - Smart appliance scheduling (hot water, pool pumps, EV charging)
   - Peak demand reduction strategies
   - Grid export limiting compliance

### Common Australian Scenarios

#### Scenario 1: Peak Demand Management
```python
# EMHASS optimization for peak demand reduction
optimization_config = {
    "peak_demand_limit": 8.0,  # kW - avoid high demand charges
    "load_shedding_priority": [
        "pool_pump",      # Low priority
        "hot_water",      # Can defer heating
        "ev_charger",     # Flexible charging
        "air_conditioning"  # High priority - comfort
    ]
}
```

#### Scenario 2: Export Limiting
```python
# Configuration for network export limits
export_config = {
    "max_export_kw": 5.0,  # Network limit
    "export_strategy": "battery_first",  # Store before exporting
    "curtailment_method": "inverter_control"
}
```

## Integration with Home Assistant

### Required Sensors
```yaml
# Essential sensors for EMHASS operation
sensors:
  - platform: modbus  # Smart meter
    name: "Grid Import Power"
    unit: "W"
    
  - platform: modbus  # Solar inverter
    name: "Solar Production"
    unit: "W"
    
  - platform: modbus  # Battery system
    name: "Battery SOC"
    unit: "%"
    
  - platform: template  # Calculated load
    name: "House Load"
    unit: "W"
    value_template: >
      {{ states('sensor.grid_import')|float + 
         states('sensor.solar_production')|float }}
```

### EMHASS Add-on Configuration
```yaml
# Add-on configuration
data_path: "/share/emhass/"
costfun: "profit"  # or "cost", "self-consumption"
logging_level: "INFO"

# Optimization parameters
delta_forecast: 48  # Hours ahead to forecast
freq: 30  # Optimization frequency (minutes)
```

## Australian Regulations and Standards

### AS/NZS 4777 Compliance
- **Voltage regulation**: EMHASS respects grid voltage limits
- **Frequency response**: Automatic curtailment during grid events
- **Export limiting**: Configurable limits for network compliance

### Network Service Provider Rules
- **Western Power**: 5kW export limit (typical)
- **Ausgrid**: Dynamic export limits in some areas
- **Energex**: Time-based export restrictions
- **SA Power Networks**: Export limiting trials

## Advanced Features

### Weather Integration
```yaml
# Weather-based optimization
weather_config:
  source: "Bureau of Meteorology"
  api_key: "your_bom_api_key"
  location: "Sydney"
  forecast_days: 3
  
# Cloud cover impact on solar
cloud_factor:
  clear: 1.0
  partly_cloudy: 0.8
  overcast: 0.3
  rain: 0.1
```

### EV Charging Integration
```yaml
# Electric vehicle charging optimization
ev_config:
  charger_power: 7.4  # kW single-phase
  battery_capacity: 75  # kWh
  daily_usage: 50      # km average
  efficiency: 6        # km/kWh
  
  # Charging preferences
  must_be_ready: "07:00"  # Must be charged by
  prefer_solar: true      # Prefer daytime charging
  allow_grid: true        # Allow grid charging if needed
```

## Troubleshooting Common Issues

### EMHASS Not Optimizing
1. **Check sensor data**: Ensure all required sensors are providing data
2. **Verify configuration**: Check units and sensor names match
3. **Review optimization logs**: Look for mathematical solver errors
4. **Network connectivity**: Ensure weather API access

### Poor Optimization Results
1. **Historical data**: Allow 1-2 weeks for learning patterns
2. **Tariff accuracy**: Verify pricing data matches actual bills
3. **Load forecasting**: Check if load predictions match reality
4. **Weather forecasts**: Ensure location and API are correct

## Jerry's Implementation Recommendations

### Phase 1: Basic Setup
1. Install Home Assistant with energy monitoring
2. Configure EMHASS add-on with basic settings
3. Set up essential sensors (grid, solar, battery)
4. Configure local electricity tariff

### Phase 2: Optimization
1. Add weather forecasting integration
2. Configure load scheduling for major appliances
3. Implement battery optimization strategies
4. Set up export limiting if required

### Phase 3: Advanced Features
1. EV charging integration
2. Demand charge optimization
3. Multi-zone heating/cooling control
4. Grid services participation (VPP programs)

## Resources and Documentation

### Official Resources
- **EMHASS GitHub**: https://github.com/davidusb-geek/emhass
- **Home Assistant Integration**: https://github.com/davidusb-geek/emhass-add-on
- **Documentation**: https://emhass.readthedocs.io/

### Australian Energy Resources
- **AEMO Data**: http://www.nemweb.com.au/
- **Solar Forecasting**: http://www.bom.gov.au/
- **Network Information**: Local DNSP websites
- **Retailer APIs**: Check with your electricity retailer

### Community Support
- **Home Assistant Community**: Australian Energy Management forum
- **EMHASS Discussions**: GitHub discussions and issues
- **Australian Solar Forums**: SolarQuotes, Whirlpool Energy
# Vehicle-to-Grid (V2G) Integration Guide

## Overview

Vehicle-to-Grid (V2G) technology enables electric vehicles to not only consume electricity but also supply power back to the grid or home. In Australia, V2G represents a significant opportunity for energy arbitrage, grid services, and home backup power using the large battery capacity of modern EVs.

## V2G Technology in Australia

### Current V2G Landscape
- **Nissan LEAF**: First production V2G vehicle available in Australia
- **Mitsubishi Outlander PHEV**: V2H (Vehicle-to-Home) capable
- **Hyundai IONIQ 5**: V2L (Vehicle-to-Load) with adapter
- **Future vehicles**: Most manufacturers planning V2G capability by 2025

### Australian V2G Trials
- **ANU Trial (Canberra)**: Research on grid services and home backup
- **UTS/Nissan Trial (Sydney)**: Commercial building integration
- **ARENA Projects**: Multiple funded V2G demonstration projects
- **Horizon Power (WA)**: Remote community grid support trials

### Regulatory Environment
- **AEMO Integration**: Working on V2G grid service standards
- **AS/NZS Standards**: Developing V2G safety and interoperability standards
- **Network Approvals**: DNSP approval processes for grid-connected V2G
- **Metering Requirements**: Separate import/export metering for V2G services

## V2G System Architecture

### Hardware Components
```
EV Battery (40-100kWh)
     ↕
CHAdeMO/CCS V2G Charger (10-22kW)
     ↕
V2G Controller/Inverter
     ↕
Home Energy Management System
     ↕
Grid Connection/Smart Meter
```

### Software Integration Stack
```python
# V2G control system architecture
class V2GController:
    def __init__(self, vehicle_connector, home_ems, grid_interface):
        self.vehicle = vehicle_connector      # Vehicle communication
        self.home_ems = home_ems            # Home energy management
        self.grid = grid_interface          # Grid services interface
        self.battery_capacity = 0           # Vehicle battery capacity
        self.min_soc = 0.2                 # Minimum charge for driving
        self.max_discharge_rate = 10        # kW maximum discharge
        
    def get_available_capacity(self):
        """Calculate available V2G capacity"""
        current_soc = self.vehicle.get_soc()
        available_soc = max(0, current_soc - self.min_soc)
        return self.battery_capacity * available_soc
        
    def optimize_charging_schedule(self, departure_time, required_soc):
        """Optimize V2G charging/discharging schedule"""
        # Implementation details below
        pass
```

## Vehicle Integration Protocols

### CHAdeMO V2G Implementation
```python
# CHAdeMO V2G communication protocol
import can
import struct

class CHAdeMOV2G:
    def __init__(self, can_interface='can0'):
        self.bus = can.interface.Bus(channel=can_interface, bustype='socketcan')
        self.vehicle_connected = False
        
    def establish_connection(self):
        """Establish V2G communication with vehicle"""
        # Send capability message
        capability_msg = can.Message(
            arbitration_id=0x108,  # CHAdeMO capability ID
            data=[0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
            is_extended_id=False
        )
        self.bus.send(capability_msg)
        
        # Wait for vehicle response
        response = self.bus.recv(timeout=5.0)
        if response and response.arbitration_id == 0x109:
            self.vehicle_connected = True
            return self.parse_vehicle_capabilities(response.data)
        return None
        
    def set_power_demand(self, power_kw):
        """Set charging (+) or discharging (-) power demand"""
        if not self.vehicle_connected:
            return False
            
        # Convert power to CHAdeMO format
        power_raw = int(power_kw * 100)  # 0.01kW resolution
        direction = 0x01 if power_kw >= 0 else 0x02  # Charge/Discharge
        
        msg_data = struct.pack('<HBBBBBb', 
                              abs(power_raw), direction, 0, 0, 0, 0, 0)
        
        power_msg = can.Message(
            arbitration_id=0x110,
            data=msg_data,
            is_extended_id=False
        )
        
        self.bus.send(power_msg)
        return True
```

### Tesla V2G Integration (Future)
```python
# Tesla V2G integration (when available)
import tesla_api

class TeslaV2G:
    def __init__(self, access_token, vehicle_id):
        self.tesla = tesla_api.TeslaAPI(access_token)
        self.vehicle_id = vehicle_id
        
    async def get_vehicle_state(self):
        """Get current vehicle state and battery level"""
        vehicle = await self.tesla.get_vehicle(self.vehicle_id)
        charge_state = await vehicle.get_charge_state()
        
        return {
            'battery_level': charge_state['battery_level'],
            'charge_limit': charge_state['charge_limit_soc'],
            'charging_state': charge_state['charging_state'],
            'est_battery_range': charge_state['est_battery_range_km'],
            'usable_battery_level': charge_state['usable_battery_level']
        }
        
    async def set_v2g_mode(self, enabled, max_discharge_percent=70):
        """Enable/disable V2G and set discharge limit"""
        # Future Tesla V2G API (hypothetical)
        return await self.tesla.set_v2g_settings(
            self.vehicle_id,
            enabled=enabled,
            max_discharge_soc=max_discharge_percent
        )
```

## Home Assistant V2G Integration

### V2G Device Configuration
```yaml
# configuration.yaml
v2g:
  platform: chademo
  device: "/dev/ttyUSB0"  # CAN interface
  scan_interval: 30
  
# V2G sensors
sensor:
  - platform: v2g
    monitored_conditions:
      - battery_soc
      - available_capacity
      - charge_rate
      - discharge_rate
      - connection_status
      - vehicle_model
      
switch:
  - platform: v2g
    switches:
      - v2g_enabled
      - emergency_backup_mode
      
number:
  - platform: v2g
    numbers:
      - max_discharge_power
      - min_departure_soc
      - backup_reserve_soc
```

### V2G Automations

#### Smart Grid Services
```yaml
# Provide grid services with V2G
automation:
  - alias: "V2G Frequency Response"
    trigger:
      - platform: numeric_state
        entity_id: sensor.grid_frequency
        below: 49.8  # Under-frequency event
        for: "00:00:05"
    condition:
      - condition: state
        entity_id: binary_sensor.ev_connected
        state: "on"
      - condition: numeric_state
        entity_id: sensor.ev_battery_soc
        above: 50  # Sufficient charge for services
    action:
      - service: number.set_value
        entity_id: number.v2g_discharge_power
        data:
          value: 5000  # 5kW frequency response
      - delay: "00:10:00"  # 10 minute response
      - service: number.set_value
        entity_id: number.v2g_discharge_power
        data:
          value: 0  # Return to normal
```

#### Home Backup Power
```yaml
# Automatic backup power during outages
automation:
  - alias: "V2G Backup Power"
    trigger:
      - platform: state
        entity_id: binary_sensor.grid_connection
        to: "off"
    condition:
      - condition: state
        entity_id: binary_sensor.ev_connected
        state: "on"
      - condition: numeric_state
        entity_id: sensor.ev_battery_soc
        above: 30  # Minimum for backup
    action:
      # Switch to backup mode
      - service: switch.turn_on
        entity_id: switch.v2g_backup_mode
        
      # Notify household
      - service: notify.mobile_app
        data:
          title: "Grid Outage - V2G Backup Active"
          message: >
            Grid power lost. EV providing backup power.
            Estimated backup time: {{ states('sensor.v2g_backup_duration') }} hours
            
      # Reduce non-essential loads
      - service: switch.turn_off
        entity_id:
          - switch.pool_pump
          - switch.hot_water
```

#### Energy Arbitrage
```yaml
# Buy low, sell high with V2G arbitrage
automation:
  - alias: "V2G Energy Arbitrage"
    trigger:
      - platform: state
        entity_id: sensor.electricity_price
    action:
      - choose:
          # Very low prices - charge vehicle
          - conditions:
              - condition: numeric_state
                entity_id: sensor.electricity_price
                below: 0.10  # 10c/kWh
              - condition: numeric_state
                entity_id: sensor.ev_battery_soc
                below: 90
            sequence:
              - service: number.set_value
                entity_id: number.v2g_charge_power
                data:
                  value: 11000  # 11kW charging
                  
          # High prices - discharge vehicle
          - conditions:
              - condition: numeric_state
                entity_id: sensor.electricity_price
                above: 0.40  # 40c/kWh
              - condition: numeric_state
                entity_id: sensor.ev_battery_soc
                above: 60  # Keep reserve for driving
              - condition: time
                after: "16:00:00"
                before: "21:00:00"  # Peak period
            sequence:
              - service: number.set_value
                entity_id: number.v2g_discharge_power
                data:
                  value: 7000  # 7kW discharge
                  
        # Default - maintain current state
        default:
          - service: number.set_value
            entity_id: number.v2g_charge_power
            data:
              value: 0
```

## Advanced V2G Strategies

### Predictive Departure Management
```python
# AI-powered departure prediction for V2G optimization
import machine_learning_models as ml
from datetime import datetime, timedelta

class DeparturePrediction:
    def __init__(self):
        self.model = ml.load_model('departure_prediction.pkl')
        self.driving_patterns = {}
        
    def predict_next_departure(self, current_time):
        """Predict when vehicle will next be needed"""
        features = {
            'hour': current_time.hour,
            'day_of_week': current_time.weekday(),
            'month': current_time.month,
            'is_weekend': current_time.weekday() >= 5,
            'recent_pattern': self.get_recent_pattern()
        }
        
        prediction = self.model.predict([features])
        confidence = self.model.predict_proba([features]).max()
        
        return {
            'departure_time': current_time + timedelta(hours=prediction[0]),
            'confidence': confidence,
            'required_soc': self.estimate_required_soc(prediction[0])
        }
    
    def estimate_required_soc(self, hours_until_departure):
        """Estimate required battery level based on typical usage"""
        daily_driving_kwh = 15  # Average daily consumption
        if hours_until_departure > 24:
            return 0.8  # 80% for multi-day trips
        elif hours_until_departure > 8:
            return 0.6  # 60% for day trips
        else:
            return 0.4  # 40% for short trips
```

### Multi-Vehicle Fleet Management
```yaml
# Manage multiple EVs for optimal V2G services
template:
  - sensor:
      - name: "Fleet V2G Capacity"
        unit_of_measurement: "kWh"
        state: >
          {% set vehicles = ['ev_1', 'ev_2', 'ev_3'] %}
          {% set total_capacity = 0 %}
          {% for vehicle in vehicles %}
            {% if states(f'binary_sensor.{vehicle}_connected') == 'on' %}
              {% set soc = states(f'sensor.{vehicle}_battery_soc') | float %}
              {% set capacity = state_attr(f'sensor.{vehicle}_battery_capacity', 'value') | float %}
              {% set available = (soc - 20) * capacity / 100 %}  # Reserve 20% for driving
              {% set total_capacity = total_capacity + available %}
            {% endif %}
          {% endfor %}
          {{ total_capacity | round(1) }}
          
  - sensor:
      - name: "Optimal V2G Schedule"
        state: "calculated"
        attributes:
          schedule: >
            {% set vehicles = ['ev_1', 'ev_2', 'ev_3'] %}
            {% set departures = {} %}
            {% for vehicle in vehicles %}
              {% if states(f'binary_sensor.{vehicle}_connected') == 'on' %}
                {% set departure = state_attr(f'sensor.{vehicle}_departure_prediction', 'time') %}
                {% set departures = departures.update({vehicle: departure}) %}
              {% endif %}
            {% endfor %}
            
            {# Sort vehicles by departure time and allocate V2G services #}
            {% set sorted_vehicles = departures.items() | sort(attribute='1') %}
            {% set schedule = {} %}
            {% for vehicle, departure in sorted_vehicles %}
              {% set hours_available = ((departure | as_timestamp) - now().timestamp()) / 3600 %}
              {% if hours_available > 4 %}  # Minimum 4 hours for V2G
                {% set schedule = schedule.update({vehicle: 'v2g_active'}) %}
              {% else %}
                {% set schedule = schedule.update({vehicle: 'charging_only'}) %}
              {% endif %}
            {% endfor %}
            {{ schedule }}
```

### Grid Service Aggregation
```python
# Aggregate multiple V2G vehicles for grid services
class V2GAggregator:
    def __init__(self):
        self.vehicles = {}
        self.grid_contracts = {}
        
    def register_vehicle(self, vehicle_id, capabilities):
        """Register a vehicle for grid services"""
        self.vehicles[vehicle_id] = {
            'max_power': capabilities['max_discharge_kw'],
            'available_energy': capabilities['available_kwh'],
            'min_soc': capabilities['min_soc_percent'],
            'departure_time': capabilities['next_departure'],
            'response_time': capabilities['response_seconds']
        }
        
    def bid_grid_services(self, service_type, duration_hours, price_per_kwh):
        """Submit aggregated bid for grid services"""
        available_vehicles = self.get_available_vehicles(duration_hours)
        total_capacity = sum(v['max_power'] for v in available_vehicles.values())
        total_energy = sum(v['available_energy'] for v in available_vehicles.values())
        
        if total_capacity >= 10:  # Minimum 10kW for grid services
            bid = {
                'service_type': service_type,  # 'frequency_response', 'peak_shaving', 'voltage_support'
                'capacity_kw': total_capacity,
                'energy_kwh': total_energy,
                'duration_hours': duration_hours,
                'price_per_kwh': price_per_kwh,
                'response_time': min(v['response_time'] for v in available_vehicles.values())
            }
            return self.submit_bid_to_aemo(bid)
        return None
        
    def distribute_grid_signal(self, signal):
        """Distribute grid service signal across vehicles"""
        total_capacity = sum(v['max_power'] for v in self.vehicles.values())
        
        for vehicle_id, vehicle in self.vehicles.items():
            vehicle_share = vehicle['max_power'] / total_capacity
            vehicle_signal = signal * vehicle_share
            self.send_signal_to_vehicle(vehicle_id, vehicle_signal)
```

## Economic Analysis

### V2G Revenue Calculations
```yaml
# Track V2G revenue streams
template:
  - sensor:
      - name: "Daily V2G Revenue"
        unit_of_measurement: "AUD"
        state: >
          {% set energy_arbitrage = states('sensor.v2g_arbitrage_profit') | float %}
          {% set grid_services = states('sensor.v2g_grid_services_payment') | float %}
          {% set backup_value = states('sensor.v2g_backup_value') | float %}
          {{ (energy_arbitrage + grid_services + backup_value) | round(2) }}
          
      - name: "V2G ROI Analysis"
        state: "calculated"
        attributes:
          annual_revenue: >
            {{ (states('sensor.daily_v2g_revenue') | float * 365) | round(2) }}
          equipment_cost: 15000  # V2G charger and installation
          payback_years: >
            {% set daily_revenue = states('sensor.daily_v2g_revenue') | float %}
            {% set annual_revenue = daily_revenue * 365 %}
            {{ (15000 / annual_revenue) | round(1) if annual_revenue > 0 else 'N/A' }}
```

### Battery Degradation Modeling
```python
# Model battery degradation from V2G usage
class BatteryDegradationModel:
    def __init__(self, battery_chemistry='LFP'):
        self.chemistry = battery_chemistry
        self.degradation_factors = {
            'LFP': {'cycle_life': 6000, 'calendar_life': 15},  # LiFePO4
            'NCM': {'cycle_life': 3000, 'calendar_life': 10},  # Ni-Co-Mn
            'NCA': {'cycle_life': 2500, 'calendar_life': 8}    # Ni-Co-Al
        }
        
    def calculate_degradation(self, cycles_per_year, depth_of_discharge, temperature_avg):
        """Calculate annual battery degradation from V2G usage"""
        base_degradation = 1 / self.degradation_factors[self.chemistry]['calendar_life']
        
        # Cycle degradation
        cycle_degradation = cycles_per_year / self.degradation_factors[self.chemistry]['cycle_life']
        
        # Depth of discharge factor
        dod_factor = (depth_of_discharge / 100) ** 1.5
        
        # Temperature factor (degradation increases with temperature)
        temp_factor = 1 + (temperature_avg - 25) * 0.02
        
        total_degradation = (base_degradation + cycle_degradation * dod_factor) * temp_factor
        return min(total_degradation, 0.2)  # Max 20% annual degradation
```

## Safety and Standards

### AS/NZS V2G Standards
- **AS/NZS 61851.23**: Electric vehicle conductive charging - DC EV supply equipment
- **AS/NZS 61851.24**: Electric vehicle charging - Digital communication between EV and EVSE
- **AS/NZS 62196**: Plugs, socket-outlets, vehicle connectors and vehicle inlets
- **AS/NZS 4777**: Grid connection of energy systems via inverters

### Safety Implementation
```python
# Safety systems for V2G operation
class V2GSafetySystem:
    def __init__(self):
        self.safety_checks = []
        self.emergency_stop = False
        
    def register_safety_check(self, check_function, critical=True):
        """Register a safety check function"""
        self.safety_checks.append({
            'function': check_function,
            'critical': critical,
            'last_result': None,
            'failure_count': 0
        })
        
    def run_safety_checks(self):
        """Run all safety checks before V2G operation"""
        critical_failures = []
        warnings = []
        
        for check in self.safety_checks:
            try:
                result = check['function']()
                check['last_result'] = result
                
                if not result['safe']:
                    if check['critical']:
                        critical_failures.append(result['message'])
                    else:
                        warnings.append(result['message'])
                        
            except Exception as e:
                check['failure_count'] += 1
                if check['critical']:
                    critical_failures.append(f"Safety check failed: {e}")
                    
        if critical_failures:
            self.emergency_stop = True
            return {'safe': False, 'critical_failures': critical_failures}
            
        return {'safe': True, 'warnings': warnings}
        
    def emergency_disconnect(self):
        """Emergency disconnect V2G system"""
        # Immediately stop all power transfer
        # Disconnect vehicle from grid
        # Notify operators
        pass
```

## Jerry's V2G Implementation Guide

### Phase 1: Assessment and Planning
1. **Vehicle Compatibility**: Verify V2G capability or upgrade path
2. **Electrical Assessment**: Evaluate home electrical system capacity
3. **Grid Connection**: Check DNSP requirements and approval process
4. **Economic Analysis**: Calculate potential returns and payback period

### Phase 2: Infrastructure Installation
1. **V2G Charger**: Install certified bidirectional charger
2. **Grid Integration**: Implement proper metering and protection
3. **Control System**: Set up home energy management integration
4. **Safety Systems**: Install all required safety and monitoring equipment

### Phase 3: Optimization and Services
1. **Home Integration**: Optimize with solar, battery, and load management
2. **Grid Services**: Register for FCAS and other grid service markets
3. **Aggregation**: Join V2G aggregation services for better returns
4. **Monitoring**: Continuous optimization and performance tracking

### Common V2G Applications for Australian Homes
1. **Peak Shaving**: Reduce expensive peak period consumption
2. **Solar Storage**: Store excess solar in vehicle during day, use at night
3. **Backup Power**: Provide backup during blackouts and emergencies
4. **Grid Services**: Participate in frequency control and voltage support
5. **Energy Arbitrage**: Buy low, sell high with time-of-use pricing
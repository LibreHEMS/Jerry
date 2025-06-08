# EMHASS Information

## Json file of all current EMHASS parameters

```json
{
  "Local": {
    "costfun": {
      "friendly_name": "Cost function",
      "Description": "Define the type of cost function.",
      "input": "select",
      "select_options": [
        "profit",
        "cost",
        "self-consumption"
      ],
      "default_value": "profit"
    },
    "sensor_power_photovoltaics": {
      "friendly_name": "Sensor power photovoltaic",
      "Description": "This is the name of the photovoltaic power-produced sensor in Watts from Home Assistant. For example: ‘sensor.power_photovoltaics’.",
      "input": "string",
      "default_value": "sensor.power_photovoltaics"
    },
    "sensor_power_photovoltaics_forecast": {
      "friendly_name": "Sensor power photovoltaic forecast",
      "Description": "This is the name of the photovoltaic forecast sensor in Watts from Home Assistant. For example: ‘sensor.p_pv_forecast’.",
      "input": "string",
      "default_value": "sensor.p_pv_forecast"
    },
    "sensor_power_load_no_var_loads": {
      "friendly_name": "Sensor power loads with no variable loads",
      "Description": "The name of the household power consumption sensor in Watts from Home Assistant. The deferrable loads that we will want to include in the optimization problem should be subtracted from this sensor in HASS. For example: ‘sensor.power_load_no_var_loads’",
      "input": "string",
      "default_value": "sensor.power_load_no_var_loads"
    },
    "sensor_replace_zero": {
      "friendly_name": "Sensor to replace NAN values with 0s",
      "Description": "The list of retrieved variables that we would want to replace NANs (if they exist) with zeros.",
      "input": "array.string",
      "default_value": "sensor.power_photovoltaics"
    },
    "sensor_linear_interp": {
      "friendly_name": "Sensor to replace NAN values with linear interpolation",
      "Description": "The list of retrieved variables that we would want to interpolate NANs values using linear interpolation",
      "input": "array.string",
      "default_value": "sensor.power_photovoltaics"
    },
    "continual_publish": {
      "friendly_name": "Continually publish optimization results",
      "Description": "set to True to save entities to .json after an optimization run. Then automatically republish the saved entities (with updated current state value) every freq minutes. entity data saved to data_path/entities.",
      "input": "boolean",
      "default_value": false
    },
    "logging_level": {
      "friendly_name": "Logging level",
      "Description": "DEBUG provides detailed diagnostic information, INFO gives general operational messages, WARNING highlights potential issues, and ERROR indicates critical problems that may disrupt functionality.",
      "input": "select",
      "select_options": [
        "INFO",
        "DEBUG",
        "WARNING",
        "ERROR"
      ],
      "default_value": "INFO"
    }
  },
  "System": {
    "optimization_time_step": {
      "friendly_name": "Optimization steps per minute (timesteps)",
      "Description": "The time step to resample retrieved data from hass. This parameter is given in minutes. It should not be defined too low or you will run into memory problems when defining the Linear Programming optimization. Defaults to 30",
      "input": "int",
      "default_value": 30
    },
    "historic_days_to_retrieve": {
      "friendly_name": "Historic days to retrieve",
      "Description": "We will retrieve data from now to days_to_retrieve days. Defaults to 2",
      "input": "int",
      "default_value": 2
    },
    "load_negative": {
      "friendly_name": "Load negative values",
      "Description": "Set this parameter to True if the retrieved load variable is negative by convention. Defaults to False",
      "input": "boolean",
      "default_value": false
    },
    "set_zero_min": {
      "friendly_name": "Remove Negatives",
      "Description": "Set this parameter to True to give a special treatment for a minimum value saturation to zero for power consumption data. Values below zero are replaced by nans. Defaults to True.",
      "input": "boolean",
      "default_value": true
    },
    "method_ts_round": {
      "friendly_name": "Timestamp rounding method",
      "Description": "Set the method for timestamp rounding, options are: first, last and nearest.",
      "input": "select",
      "select_options": [
        "nearest",
        "first",
        "last"
      ],
      "default_value": "nearest"
    },
    "delta_forecast_daily": {
      "friendly_name": "Number of forecasted days",
      "Description": "The number of days for forecasted data. Defaults to 1.",
      "input": "int",
      "default_value": 1
    },
    "load_forecast_method": {
      "friendly_name": "Load forecast method",
      "Description": "The load forecast method that will be used. The options are ‘csv’ to load a CSV file or ‘naive’ for a simple 1-day persistence model.",
      "input": "select",
      "select_options": [
        "typical",
        "naive",
        "mlforecaster",
        "csv"
      ],
      "default_value": "typical"
    },
    "set_total_pv_sell": {
      "friendly_name": "PV straight to grid",
      "Description": "Set this parameter to true to consider that all the PV power produced is injected to the grid. No direct self-consumption. The default is false, for a system with direct self-consumption.",
      "input": "boolean",
      "default_value": false
    },
    "lp_solver": {
      "friendly_name": "Linear programming solver",
      "Description": "Set the name of the linear programming solver that will be used. Defaults to ‘COIN_CMD’. The options are ‘PULP_CBC_CMD’, ‘GLPK_CMD’, ‘HiGHS’, and ‘COIN_CMD’.",
      "input": "select",
      "select_options": [
        "default",
        "COIN_CMD",
        "PULP_CBC_CMD",
        "GLPK_CMD",
        "HiGHS"
      ],
      "default_value": "COIN_CMD"
    },
    "lp_solver_path": {
      "friendly_name": "Linear programming solver program path",
      "Description": "Set the path to the LP solver. Defaults to ‘/usr/bin/cbc’.",
      "input": "text",
      "default_value": "/usr/bin/cbc"
    },
    "num_threads": {
      "friendly_name": "Number of threads to use for the LP solver",
      "Description": "Set the number of threads for the LP solver to use, when supported by the solver. Defaults to 0 (autodetect)",
      "input": "int",
      "default_value": 0
    },
    "lp_solver_timeout": {
      "friendly_name": "Linear programming solver timeout",
      "Description": "Set the maximum time (in seconds) for the LP solver. Defaults to 45.",
      "input": "int",
      "default_value": 45
    },
    "weather_forecast_method": {
      "friendly_name": "Weather forecast method",
      "Description": "This will define the weather forecast method that will be used. options are 'open-meteo', 'Solcast', 'solar.forecast' (forecast.solar) and 'csv' to load a CSV file. When loading a CSV file this will be directly considered as the PV power forecast in Watts.",
      "input": "select",
      "select_options": [
        "open-meteo",
        "solcast",
        "solar.forecast",
        "csv"
      ],
      "default_value": "open-meteo"
    },
    "open_meteo_cache_max_age": {
      "friendly_name": "Open-Meteo Cache Max Age",
      "Description": "The maximum age, in minutes, of the cached open-meteo json response, after which a new version will be fetched from Open-Meteo. Defaults to 30.",
      "input": "int",
      "default_value": 30
    },
    "maximum_power_from_grid": {
      "friendly_name": "Max power from grid",
      "Description": "The maximum power that can be supplied by the utility grid in Watts (consumption). Defaults to 9000.",
      "input": "int",
      "default_value": 9000
    },
    "maximum_power_to_grid": {
      "friendly_name": "Max export power to grid",
      "Description": "The maximum power that can be supplied to the utility grid in Watts (injection). Defaults to 9000.",
      "input": "int",
      "default_value": 9000
    },
    "inverter_is_hybrid": {
      "friendly_name": "Inverter is a hybrid",
      "Description": "Set to True to consider that the installation inverter is hybrid for PV and batteries (Default False)",
      "input": "boolean",
      "default_value": false
    },
    "compute_curtailment": {
      "friendly_name": "Set compute curtailment (grid export limit)",
      "Description": "Set to True to compute a special PV curtailment variable (Default False)",
      "input": "boolean",
      "default_value": false
    }
  },
  "Tariff": {
    "load_cost_forecast_method": {
      "friendly_name": "Load cost method",
      "Description": "Define the method that will be used for load cost forecast. The options are ‘hp_hc_periods’ for peak and non-peak hours contracts, and ‘csv’ to load custom cost from CSV file.",
      "input": "select",
      "select_options": [
        "hp_hc_periods",
        "csv"
      ],
      "default_value": "hp_hc_periods"
    },
    "load_peak_hour_periods": {
      "friendly_name": "List peak hour periods",
      "Description": "A list of peak hour periods for load consumption from the grid. This is useful if you have a contract with peak and non-peak hours.",
      "input": "array.time",
      "default_value": {
        "period_hp_template": [{ "start": "02:54" }, { "end": "15:24" }]
      },
      "requires": {
        "load_cost_forecast_method": "hp_hc_periods"
      }
    },
    "load_peak_hours_cost": {
      "friendly_name": "Peak hours electrical energy cost",
      "Description": "The cost of the electrical energy during peak hours",
      "input": "float",
      "requires": {
        "load_cost_forecast_method": "hp_hc_periods"
      },
      "default_value": 0.1907
    },
    "load_offpeak_hours_cost": {
      "friendly_name": "Off-peak hours electrical energy cost",
      "Description": "The cost of the electrical energy during off-peak hours",
      "input": "float",
      "requires": {
        "load_cost_forecast_method": "hp_hc_periods"
      },
      "default_value": 0.1419
    },
    "production_price_forecast_method": {
      "friendly_name": "PV power production price forecast method",
      "Description": "Define the method that will be used for PV power production price forecast. This is the price that is paid by the utility for energy injected into the grid. The options are ‘constant’ for a constant fixed value or ‘csv’ to load custom price forecasts from a CSV file.",
      "input": "select",
      "select_options": [
        "constant",
        "csv"
      ],
      "default_value": "constant"
    },
    "photovoltaic_production_sell_price": {
      "friendly_name": "Constant PV power production price",
      "Description": "The paid price for energy injected to the grid from excess PV production in €/kWh.",
      "input": "float",
      "default_value": 0.1419,
      "requires": {
        "production_price_forecast_method": "constant"
      }
    }
  },
  "Solar System (PV)": {
    "set_use_pv": {
      "friendly_name": "Enable PV system",
      "Description": "Set to True if we should consider an solar PV system. Defaults to False",
      "input": "boolean",
      "default_value": false
    },
    "set_use_adjusted_pv": {
      "friendly_name": "Enable adjusted PV system",
      "Description": "Set to True if we should consider an adjusted solar PV system. Defaults to False",
      "input": "boolean",
      "default_value": false
    },
    "adjusted_pv_regression_model": {
      "friendly_name": "Regression model for adjusted PV",
      "Description": "Set the type of regression model that will be used to adjust the solr PV production to local conditions. Defaults to LassoRegression",
      "input": "select",
      "select_options": [
        "LinearRegression",
        "RidgeRegression",
        "LassoRegression",
        "RandomForestRegression",
        "GradientBoostingRegression",
        "AdaBoostRegression"
      ],
      "default_value": "LassoRegression"
    },
    "adjusted_pv_solar_elevation_threshold": {
      "friendly_name": "Solar elevation threshold",
      "Description": "This is the solar elevation threshold parameter used to identify the early morning or late evening periods. Defaults to 10.",
      "input": "int",
      "default_value": 10
    },
    "pv_module_model": {
      "friendly_name": "PV module model name",
      "Description": "The PV module model. This parameter can be a list of items to enable the simulation of mixed orientation systems.",
      "input": "array.string",
      "input_attributes": "_'s",
      "default_value": "CSUN_Eurasia_Energy_Systems_Industry_and_Trade_CSUN295_60M"
    },
    "pv_inverter_model": {
      "friendly_name": "The PV inverter model name",
      "Description": "The PV inverter model.  This parameter can be a list of items to enable the simulation of mixed orientation systems.",
      "input": "array.string",
      "input_attributes": "_'s",
      "default_value": "Fronius_International_GmbH__Fronius_Primo_5_0_1_208_240__240V_"
    },
    "surface_tilt": {
      "friendly_name": "The PV panel tilt",
      "Description": "The tilt angle of your solar panels. Defaults to 30. This parameter can be a list of items to enable the simulation of mixed orientation systems.",
      "input": "array.int",
      "default_value": 30
    },
    "surface_azimuth": {
      "friendly_name": "The PV azimuth (direction)",
      "Description": "The azimuth of your PV installation. Defaults to 205. This parameter can be a list of items to enable the simulation of mixed orientation systems.",
      "input": "array.int",
      "default_value": 205
    },
    "modules_per_string": {
      "friendly_name": "Number of modules per string",
      "Description": "The number of modules per string. Defaults to 16. This parameter can be a list of items to enable the simulation of mixed orientation systems.",
      "input": "array.int",
      "default_value": 16
    },
    "strings_per_inverter": {
      "friendly_name": "Number of strings per inverter",
      "Description": "The number of used strings per inverter. Defaults to 1. This parameter can be a list of items to enable the simulation of mixed orientation systems.",
      "input": "array.int",
      "default_value": 1
    }
  },
  "Deferrable Loads": {
    "number_of_deferrable_loads": {
      "friendly_name": "Number of deferrable loads",
      "Description": "Define the number of deferrable loads (appliances to shift) to consider. Defaults to 2.",
      "input": "int",
      "default_value": 2
    },
    "nominal_power_of_deferrable_loads": {
      "friendly_name": "Deferrable load nominal power",
      "Description": "The nominal (calculated max) power for each deferrable load in Watts.",
      "input": "array.float",
      "default_value": 3000.0
    },
    "minimum_power_of_deferrable_loads": {
      "friendly_name": "Deferrable load minimum power",
      "Description": "The minimum power for each deferrable load in Watts.",
      "input": "array.float",
      "default_value": 0.0
    },
    "operating_hours_of_each_deferrable_load": {
      "friendly_name": "Deferrable load operating hours",
      "Description": "The total number of hours that each deferrable load should operate",
      "input": "array.int",
      "default_value": 0
    },
    "treat_deferrable_load_as_semi_cont": {
      "friendly_name": "Deferrable load as semi-continuous (on/off) variable",
      "Description": "Semi-continuous variables (True) are variables that must take a value that can be either their maximum or minimum/zero (for example On = Maximum load, Off = 0 W). Non semi-continuous (which means continuous) variables (False) can take any values between their maximum and minimum",
      "input": "array.boolean",
      "default_value": true
    },
    "set_deferrable_load_single_constant": {
      "friendly_name": "Deferrable load run single constant per optimization",
      "Description": "Define if we should set each deferrable load as a constant fixed value variable with just one startup for each optimization task",
      "input": "array.boolean",
      "default_value": false
    },
    "set_deferrable_startup_penalty": {
      "friendly_name": "Set deferrable startup penalty",
      "Description": "For penalty P, each time the deferrable load turns on will incur an additional cost of P * number_of_deferrable_loads * cost_of_electricity at that time",
      "input": "array.float",
      "default_value": 0.0
    },
    "start_timesteps_of_each_deferrable_load": {
      "friendly_name": "Deferrable start timestamp",
      "Description": "The timestep as from which each deferrable load is allowed to operate (if you don’t want the deferrable load to use the whole optimization time window). If you specify a value of 0 (or negative), the deferrable load will be optimized as from the beginning of the complete prediction horizon window.",
      "input": "array.int",
      "default_value": 0
    },
    "end_timesteps_of_each_deferrable_load": {
      "friendly_name": "Deferrable end timestamp",
      "Description": "The timestep before which each deferrable load should operate. The deferrable load is not allowed to operate after the specified time step. If a value of 0 (or negative) is provided, the deferrable load is allowed to operate in the complete optimization window)",
      "input": "array.int",
      "default_value": 0
    }
  },
  "Battery": {
    "set_use_battery": {
      "friendly_name": "Enable Battery",
      "Description": "Set to True if we should consider an energy storage device such as a Li-Ion battery. Defaults to False",
      "input": "boolean",
      "default_value": false
    },
    "set_nocharge_from_grid": {
      "friendly_name": "Forbid charging battery from grid",
      "Description": "Set this to true if you want to forbid charging the battery from the grid. The battery will only be charged from excess PV",
      "input": "boolean",
      "default_value": false
    },
    "set_nodischarge_to_grid": {
      "friendly_name": "Forbid battery discharge to the grid",
      "Description": "Set this to true if you want to forbid discharging battery power to the grid.",
      "input": "boolean",
      "default_value": true
    },
    "set_battery_dynamic": {
      "friendly_name": "Set Battery dynamic (dis)charge power limiting",
      "Description": "Set a power dynamic limiting condition to the battery power. This is an additional constraint on the battery dynamic in power per unit of time (timestep), which allows you to set a percentage of the battery’s nominal full power as the maximum power allowed for (dis)charge.",
      "input": "boolean",
      "default_value": false
    },
    "battery_dynamic_max": {
      "friendly_name": "Maximum percentage of battery discharge per timestep",
      "Description": "The maximum positive (for discharge) battery power dynamic. This is the allowed power variation (in percentage) of battery maximum power per unit of timestep",
      "input": "float",
      "default_value": 0.9,
      "requires": {
        "set_battery_dynamic": true
      }
    },
    "battery_dynamic_min": {
      "friendly_name": "Maximum percentage of battery charge per timestep",
      "Description": "The maximum negative (for charge) battery power dynamic. This is the allowed power variation (in percentage) of battery maximum power per timestep.",
      "input": "float",
      "default_value": -0.9,
      "requires": {
        "set_battery_dynamic": true
      }
    },
    "weight_battery_discharge": {
      "friendly_name": "Add cost weight for battery discharge",
      "Description": "An additional weight (currency/ kWh) applied in the cost function to battery usage for discharging",
      "input": "float",
      "default_value": 0.0
    },
    "weight_battery_charge": {
      "friendly_name": "Add cost weight for battery charge",
      "Description": "An additional weight (currency/ kWh) applied in the cost function to battery usage for charging",
      "input": "float",
      "default_value": 0.0
    },
    "battery_discharge_power_max": {
      "friendly_name": "Max battery discharge power",
      "Description": "The maximum discharge power in Watts",
      "input": "int",
      "default_value": 1000
    },
    "battery_charge_power_max": {
      "friendly_name": "Max battery charge power",
      "Description": "The maximum charge power in Watts",
      "input": "int",
      "default_value": 1000
    },
    "battery_discharge_efficiency": {
      "friendly_name": "Battery discharge efficiency",
      "Description": "The discharge efficiency. (percentage/100)",
      "input": "float",
      "default_value": 0.95
    },
    "battery_charge_efficiency": {
      "friendly_name": "Battery charge efficiency",
      "Description": "The charge efficiency. (percentage/100)",
      "input": "float",
      "default_value": 0.95
    },
    "battery_nominal_energy_capacity": {
      "friendly_name": "Battery total capacity",
      "Description": "The total capacity of the battery stack in Wh",
      "input": "int",
      "default_value": 5000
    },
    "battery_minimum_state_of_charge": {
      "friendly_name": "Minimum Battery charge percentage",
      "Description": "The minimum allowable battery state of charge. (percentage/100)",
      "input": "float",
      "default_value": 0.3
    },
    "battery_maximum_state_of_charge": {
      "friendly_name": "Maximum Battery charge percentage",
      "Description": "The maximum allowable battery state of charge. (percentage/100)",
      "input": "float",
      "default_value": 0.9
    },
    "battery_target_state_of_charge": {
      "friendly_name": "Battery desired percentage after optimization",
      "Description": "The desired battery state of charge at the end of each optimization cycle. (percentage/100)",
      "input": "float",
      "default_value": 0.6
    }
  }
}
```

## here is the emhass parameter associations from old (legacy_parameter_name) to new (parameter)

```csv
config_categorie,legacy_parameter_name,parameter,list_name 
retrieve_hass_conf,freq,optimization_time_step
retrieve_hass_conf,days_to_retrieve,historic_days_to_retrieve
retrieve_hass_conf,var_PV,sensor_power_photovoltaics
retrieve_hass_conf,var_PV_forecast,sensor_power_photovoltaics_forecast
retrieve_hass_conf,var_load,sensor_power_load_no_var_loads
retrieve_hass_conf,load_negative,load_negative
retrieve_hass_conf,set_zero_min,set_zero_min
retrieve_hass_conf,var_replace_zero,sensor_replace_zero,list_sensor_replace_zero
retrieve_hass_conf,var_interp,sensor_linear_interp,list_sensor_linear_interp
retrieve_hass_conf,method_ts_round,method_ts_round
retrieve_hass_conf,continual_publish,continual_publish
params_secrets,time_zone,time_zone
params_secrets,lat,Latitude
params_secrets,lon,Longitude
params_secrets,alt,Altitude
optim_conf,costfun,costfun
optim_conf,logging_level,logging_level
optim_conf,set_use_pv,set_use_pv
optim_conf,set_use_adjusted_pv,set_use_adjusted_pv
optim_conf,adjusted_pv_regression_model,adjusted_pv_regression_model
optim_conf,adjusted_pv_solar_elevation_threshold,adjusted_pv_solar_elevation_threshold
optim_conf,set_use_battery,set_use_battery
optim_conf,num_def_loads,number_of_deferrable_loads
optim_conf,P_deferrable_nom,nominal_power_of_deferrable_loads,list_nominal_power_of_deferrable_loads
optim_conf,minimum_power_of_deferrable_loads,minimum_power_of_deferrable_loads
optim_conf,def_total_hours,operating_hours_of_each_deferrable_load,list_operating_hours_of_each_deferrable_load
optim_conf,treat_def_as_semi_cont,treat_deferrable_load_as_semi_cont,list_treat_deferrable_load_as_semi_cont
optim_conf,set_def_constant,set_deferrable_load_single_constant,list_set_deferrable_load_single_constant
optim_conf,def_start_penalty,set_deferrable_startup_penalty,list_set_deferrable_startup_penalty
optim_conf,delta_forecast,delta_forecast_daily
optim_conf,load_forecast_method,load_forecast_method
optim_conf,load_cost_forecast_method,load_cost_forecast_method
optim_conf,load_cost_hp,load_peak_hours_cost
optim_conf,load_cost_hc,load_offpeak_hours_cost
optim_conf,prod_price_forecast_method,production_price_forecast_method
optim_conf,prod_sell_price,photovoltaic_production_sell_price
optim_conf,set_total_pv_sell,set_total_pv_sell
optim_conf,lp_solver,lp_solver
optim_conf,lp_solver_path,lp_solver_path
optim_conf,lp_solver_timeout,lp_solver_timeout
optim_conf,num_threads,num_threads
optim_conf,set_nocharge_from_grid,set_nocharge_from_grid
optim_conf,set_nodischarge_to_grid,set_nodischarge_to_grid
optim_conf,set_battery_dynamic,set_battery_dynamic
optim_conf,battery_dynamic_max,battery_dynamic_max
optim_conf,battery_dynamic_min,battery_dynamic_min
optim_conf,weight_battery_discharge,weight_battery_discharge
optim_conf,weight_battery_charge,weight_battery_charge
optim_conf,weather_forecast_method,weather_forecast_method
optim_conf,open_meteo_cache_max_age,open_meteo_cache_max_age
optim_conf,def_start_timestep,start_timesteps_of_each_deferrable_load,list_start_timesteps_of_each_deferrable_load
optim_conf,def_end_timestep,end_timesteps_of_each_deferrable_load,list_end_timesteps_of_each_deferrable_load
optim_conf,list_hp_periods,load_peak_hour_periods
plant_conf,P_from_grid_max,maximum_power_from_grid
plant_conf,P_to_grid_max,maximum_power_to_grid
plant_conf,module_model,pv_module_model,list_pv_module_model
plant_conf,inverter_model,pv_inverter_model,list_pv_inverter_model
plant_conf,surface_tilt,surface_tilt,list_surface_tilt
plant_conf,surface_azimuth,surface_azimuth,list_surface_azimuth
plant_conf,modules_per_string,modules_per_string,list_modules_per_string
plant_conf,strings_per_inverter,strings_per_inverter,list_strings_per_inverter
plant_conf,inverter_is_hybrid,inverter_is_hybrid
plant_conf,compute_curtailment,compute_curtailment
plant_conf,Pd_max,battery_discharge_power_max
plant_conf,Pc_max,battery_charge_power_max
plant_conf,eta_disch,battery_discharge_efficiency
plant_conf,eta_ch,battery_charge_efficiency
plant_conf,Enom,battery_nominal_energy_capacity
plant_conf,SOCmin,battery_minimum_state_of_charge
plant_conf,SOCmax,battery_maximum_state_of_charge
plant_conf,SOCtarget,battery_target_state_of_charge
```

## EMHASS README

````markdown
<br>
<p align="left">
EHMASS is a Python module designed to optimize your home energy interfacing with Home Assistant.
</p>

## Introduction

EMHASS (Energy Management for Home Assistant) is an optimization tool designed
for residential households. The package uses a Linear Programming approach to
optimize energy usage while considering factors such as electricity prices,
power generation from solar panels, and energy storage from batteries. EMHASS
provides a high degree of configurability, making it easy to integrate with Home
Assistant and other smart home systems. Whether you have solar panels, energy
storage, or just a controllable load, EMHASS can provide an optimized daily
schedule for your devices, allowing you to save money and minimize your
environmental impact.

The complete documentation for this package is
[available here](https://emhass.readthedocs.io/en/latest/).

## What is Energy Management for Home Assistant (EMHASS)?

EMHASS and Home Assistant provide a comprehensive energy management solution
that can optimize energy usage and reduce costs for households. By integrating
these two systems, households can take advantage of advanced energy management
features that provide significant cost savings, increased energy efficiency, and
greater sustainability.

EMHASS is a powerful energy management tool that generates an optimization plan
based on variables such as solar power production, energy usage, and energy
costs. The plan provides valuable insights into how energy can be better managed
and utilized in the household. Even if households do not have all the necessary
equipment, such as solar panels or batteries, EMHASS can still provide a minimal
use case solution to optimize energy usage for controllable/deferrable loads.

Home Assistant provides a platform for the automation of household devices based
on the optimization plan generated by EMHASS. This includes devices such as
batteries, pool pumps, hot water heaters, and electric vehicle (EV) chargers. By
automating EV charging and other devices, households can take advantage of
off-peak energy rates and optimize their EV charging schedule based on the
optimization plan generated by EMHASS.

One of the main benefits of integrating EMHASS and Home Assistant is the ability
to customize and tailor the energy management solution to the specific needs and
preferences of each household. With EMHASS, households can define their energy
management objectives and constraints, such as maximizing self-consumption or
minimizing energy costs, and the system will generate an optimization plan
accordingly. Home Assistant provides a platform for the automation of devices
based on the optimization plan, allowing households to create a fully customized
and optimized energy management solution.

Overall, the integration of EMHASS and Home Assistant offers a comprehensive
energy management solution that provides significant cost savings, increased
energy efficiency, and greater sustainability for households. By leveraging
advanced energy management features and automation capabilities, households can
achieve their energy management objectives while enjoying the benefits of more
efficient and sustainable energy usage, including optimized EV charging
schedules.

The package flow can be graphically represented as follows:

![](https://raw.githubusercontent.com/davidusb-geek/emhass/master/docs/images/ems_schema.png)

## Configuration and Installation

The package is meant to be highly configurable with an object-oriented modular
approach and a main configuration file defined by the user. EMHASS was designed
to be integrated with Home Assistant, hence its name. Installation instructions
and example Home Assistant automation configurations are given below.

You must follow these steps to make EMHASS work properly:

1. Install and run EMHASS.
   - There are multiple methods of installing and Running EMHASS. See
     [Installation Method](#Installation-Methods) below to pick a method that
     best suits your use case.

2. Define all the parameters in the configuration file _(`config.json`)_ or
   configuration page _(`YOURIP:5000/configuration`)_.
   - Since EMHASS v0.12.0: the default configuration does not need to retrieve
     any data from Home Assistant! After installing and running the add-on,
     EMHASS should start and it will be ready to launch an optimization.
   - See the description for each parameter in the
     [configuration](https://emhass.readthedocs.io/en/latest/config.html) docs.
   - EMHASS has a default configuration with 2 deferrable loads, no solar PV, no
     batteries and a basic load power forecasting method.
     - If you want to consider solar PV and more advanced load power forecast
       methods, you will need to define the main data entering EMHASS. This will
       be the Home Assistant sensor/variable `sensor.power_load_no_var_loads`,
       for the load power of your household excluding the power of the
       deferrable loads that you want to optimize, and the sensor/variable
       `sensor.power_photovoltaics` for the name of your Home Assistant variable
       containing the PV produced power (if solar PV is activated).
     - If you have a PV installation then this dedicated web app can be useful
       for finding your inverter and solar panel models:
       [https://emhass-pvlib-database.streamlit.app/](https://emhass-pvlib-database.streamlit.app/)

3. Launch the optimization and check the results.
   - This can be done manually using the buttons in the web UI
   - Or with a `curl` command like this:
     `curl -i -H 'Content-Type:application/json' -X POST -d '{}' http://localhost:5000/action/dayahead-optim`.

4. If you’re satisfied with the optimization results then you can set the
   optimization and data publish task commands in an automation.
   - You can read more about this in the [usage](#usage) section below.

5. The final step is to link the deferrable loads variables to real switches on
   your installation.
   - An example code for this using automations and the shell command
     integration is presented below in the [usage](#usage) section.

A more detailed workflow is given below:

![workflow.png](https://raw.githubusercontent.com/davidusb-geek/emhass/master/docs/images/workflow.png)

## Installation Methods

### Method 1) The EMHASS add-on for Home Assistant OS and supervised users

For Home Assistant OS and HA Supervised users, A
[EMHASS an add-on repository](https://github.com/davidusb-geek/emhass-add-on)
has been developed to allow the EMHASS Docker container to run as a
[Home Assistant Addon](https://www.home-assistant.io/addons/). The add-on is
more user-friendly as the Home Assistant secrets (URL and API key) are
automatically placed inside of the EMHASS container, and web server port
_(default 5000)_ is already opened.

You can find the add-on with the installation instructions here:
[https://github.com/davidusb-geek/emhass-add-on](https://github.com/davidusb-geek/emhass-add-on)

These architectures are supported: `amd64` and `aarch64` (currently `armv7` and
`armhf` are not supported).

_Note: Both EMHASS via Docker and EMHASS-Add-on contain the same Docker image.
The EMHASS-Add-on repository however, stores Home Assistant addon specific
configuration information and maintains EMHASS image version control._

### Method 2) Running EMHASS in Docker

You can also install EMHASS using Docker as a container. This can be in the same
machine as Home Assistant (if your running Home Assistant as a Docker container)
or in a different distant machine. To install first pull the latest image:

```bash
# pull Docker image
docker pull ghcr.io/davidusb-geek/emhass:latest
# run Docker image, mounting config.json and secrets_emhass.yaml from host
docker run --rm -it --restart always  -p 5000:5000 --name emhass-container -v ./config.json:/share/config.json -v ./secrets_emhass.yaml:/app/secrets_emhass.yaml ghcr.io/davidusb-geek/emhass:latest
```
````

_Note it is not recommended to install the latest EMHASS image with `:latest`
_(as you would likely want to control when you update EMHASS version)_. Instead,
find the
[latest version tag](https://github.com/davidusb-geek/emhass/pkgs/container/emhass)
(E.g: `v0.2.1`) and replace `latest`_

You can also build your image locally. For this clone this repository, and build
the image from the Dockerfile:

```bash
# git clone EMHASS repo
git clone https://github.com/davidusb-geek/emhass.git
# move to EMHASS directory 
cd emhass
# build Docker image 
# may need to set architecture tag (docker build --build-arg TARGETARCH=amd64 -t emhass-local .)
docker build -t emhass-local . 
# run built Docker image, mounting config.json and secrets_emhass.yaml from host
docker run --rm -it -p 5000:5000 --name emhass-container -v ./config.json:/share/config.json -v ./secrets_emhass.yaml:/app/secrets_emhass.yaml emhass-local
```

Before running the docker container, make sure you have a designated folder for
emhass on your host device and a `secrets_emhass.yaml` file. You can get a
example of the secrets file from
[`secrets_emhass(example).yaml`](https://github.com/davidusb-geek/emhass/blob/master/secrets_emhass(example).yaml)
file on this repository.

```bash
# cli example of creating an emhass directory and appending a secrets_emhass.yaml file inside
mkdir ~/emhass
cd ~/emhass 
cat <<EOT >> ~/emhass/secrets_emhass.yaml
hass_url: https://myhass.duckdns.org/
long_lived_token: thatverylongtokenhere
time_zone: Europe/Paris
Latitude: 45.83
Longitude: 6.86
Altitude: 4807.8
EOT
docker run --rm -it --restart always  -p 5000:5000 --name emhass-container -v ./config.json:/share/config.json -v ./secrets_emhass.yaml:/app/secrets_emhass.yaml ghcr.io/davidusb-geek/emhass:latest
```

#### Docker, things to note

- You can create a `config.json` file prior to running emhass. _(obtain a
  example from:
  [config_defaults.json](https://github.com/davidusb-geek/emhass/blob/enhass-standalone-addon-merge/src/emhass/data/config_defaults.json)_
  Alteratively, you can insert your parameters into the configuration page on
  the EMHASS web server. (for EMHASS to auto create a config.json) With either
  option, the volume mount `-v ./config.json:/share/config.json` should be
  applied to make sure your config is stored on the host device. (to be not
  deleted when the EMHASS container gets removed/image updated)*

- If you wish to keep a local, semi-persistent copy of the EMHASS-generated
  data, create a local folder on your device, then mount said folder inside the
  container.
  ```bash
  #create data folder 
  mkdir -p ~/emhass/data 
  docker run -it --restart always -p 5000:5000 -e LOCAL_COSTFUN="profit" -v ~/emhass/config.json:/app/config.json -v ~/emhass/data:/data  -v ~/emhass/secrets_emhass.yaml:/app/secrets_emhass.yaml --name DockerEMHASS <REPOSITORY:TAG>
  ```

- If you wish to set the web_server's homepage optimization diagrams to a
  timezone other than UTC, set `TZ` environment variable on docker run:
  ```bash
  docker run -it --restart always -p 5000:5000  -e TZ="Europe/Paris" -v ~/emhass/config.json:/app/config.json -v ~/emhass/secrets_emhass.yaml:/app/secrets_emhass.yaml --name DockerEMHASS <REPOSITORY:TAG>
  ```

### Method 3) Legacy method using a Python virtual environment _(Legacy CLI)_

If you wish to run EMHASS optimizations with cli commands. _(no persistent web
server session)_ you can run EMHASS via the python package alone _(not wrapped
in a Docker container)_.

With this method it is recommended to install on a virtual environment.

- Create and activate a virtual environment:
  ```bash
  python3 -m venv ~/emhassenv
  cd ~/emhassenv
  source bin/activate
  ```
- Install using the distribution files:
  ```bash
  python3 -m pip install emhass
  ```
- Create and store configuration (config.json), secret (secrets_emhass.yaml) and
  data (/data) files in the emhass dir (`~/emhassenv`)\
  Note: You may wish to copy the `config.json` (config_defaults.json),
  `secrets_emhass.yaml` (secrets_emhass(example).yaml) and/or `/scripts/` files
  from this repository to the `~/emhassenv` folder for a starting point and/or
  to run the bash scripts described below.

- To upgrade the installation in the future just use:
  ```bash
  python3 -m pip install --upgrade emhass
  ```

## Usage

### Method 1) Add-on and Docker

If using the add-on or the Docker installation, it exposes a simple webserver on
port 5000. You can access it directly using your browser. (E.g.:
http://localhost:5000)

With this web server, you can perform RESTful POST commands on multiple
ENDPOINTS with the prefix `action/*`:

- A POST call to `action/perfect-optim` to perform a perfect optimization task
  on the historical data.
- A POST call to `action/dayahead-optim` to perform a day-ahead optimization
  task of your home energy.
- A POST call to `action/naive-mpc-optim` to perform a naive Model Predictive
  Controller optimization task. If using this option you will need to define the
  correct `runtimeparams` (see further below).
- A POST call to `action/publish-data` to publish the optimization results data
  for the current timestamp.
- A POST call to `action/forecast-model-fit` to train a machine learning
  forecaster model with the passed data (see the
  [dedicated section](https://emhass.readthedocs.io/en/latest/mlforecaster.html)
  for more help).
- A POST call to `action/forecast-model-predict` to obtain a forecast from a
  pre-trained machine learning forecaster model (see the
  [dedicated section](https://emhass.readthedocs.io/en/latest/mlforecaster.html)
  for more help).
- A POST call to `action/forecast-model-tune` to optimize the machine learning
  forecaster models hyperparameters using Bayesian optimization (see the
  [dedicated section](https://emhass.readthedocs.io/en/latest/mlforecaster.html)
  for more help).

A `curl` command can then be used to launch an optimization task like this:
`curl -i -H 'Content-Type:application/json' -X POST -d '{}' http://localhost:5000/action/dayahead-optim`.

### Method 2) Legacy method using a Python virtual environment

To run a command simply use the `emhass` CLI command followed by the needed
arguments. The available arguments are:

- `--action`: This is used to set the desired action, options are:
  `perfect-optim`, `dayahead-optim`, `naive-mpc-optim`, `publish-data`,
  `forecast-model-fit`, `forecast-model-predict` and `forecast-model-tune`.
- `--config`: Define the path to the config.json file (including the yaml file
  itself)
- `--secrets`: Define secret parameter file (secrets_emhass.yaml) path
- `--costfun`: Define the type of cost function, this is optional and the
  options are: `profit` (default), `cost`, `self-consumption`
- `--log2file`: Define if we should log to a file or not, this is optional and
  the options are: `True` or `False` (default)
- `--params`: Configuration as JSON.
- `--runtimeparams`: Data passed at runtime. This can be used to pass your own
  forecast data to EMHASS.
- `--debug`: Use `True` for testing purposes.
- `--version`: Show the current version of EMHASS.
- `--root`: Define path emhass root (E.g. ~/emhass )
- `--data`: Define path to the Data files (.csv & .pkl) (E.g. ~/emhass/data/ )

For example, the following line command can be used to perform a day-ahead
optimization task:

```bash
emhass --action 'dayahead-optim' --config ~/emhass/config.json --costfun 'profit'
```

Before running any valuable command you need to modify the `config.json` and
`secrets_emhass.yaml` files. These files should contain the information adapted
to your own system. To do this take a look at the special section for this in
the [documentation](https://emhass.readthedocs.io/en/latest/config.html).

## Home Assistant Automation

To automate EMHASS with Home Assistant, we will need to define some shell
commands in the Home Assistant `configuration.yaml` file and some basic
automations in the `automations.yaml` file. In the next few paragraphs, we are
going to consider the `dayahead-optim` optimization strategy, which is also the
first that was implemented, and we will also cover how to publish the
optimization results.\
Additional optimization strategies were developed later, that can be used in
combination with/replace the `dayahead-optim` strategy, such as MPC, or to
expand the functionalities such as the Machine Learning method to predict your
household consumption. Each of them has some specificities and features and will
be considered in dedicated sections.

### Dayahead Optimization - Method 1) Add-on and docker standalone

We can use the `shell_command` integration in `configuration.yaml`:

```yaml
shell_command:
  dayahead_optim: "curl -i -H \"Content-Type:application/json\" -X POST -d '{}' http://localhost:5000/action/dayahead-optim"
  publish_data: "curl -i -H \"Content-Type:application/json\" -X POST -d '{}' http://localhost:5000/action/publish-data"
```

An alternative that will be useful when passing data at runtime (see dedicated
section), we can use the the `rest_command` instead:

```yaml
rest_command:
  url: http://127.0.0.1:5000/action/dayahead-optim
  method: POST
  headers:
    content-type: application/json
  payload: >-
    {}
```

### Dayahead Optimization - Method 2) Legacy method using a Python virtual environment

In `configuration.yaml`:

```yaml
shell_command:
  dayahead_optim: ~/emhass/scripts/dayahead_optim.sh
  publish_data: ~/emhass/scripts/publish_data.sh
```

Create the file `dayahead_optim.sh` with the following content:

```bash
#!/bin/bash
. ~/emhassenv/bin/activate
emhass --action 'dayahead-optim' --config ~/emhass/config.json
```

And the file `publish_data.sh` with the following content:

```bash
#!/bin/bash
. ~/emhassenv/bin/activate
emhass --action 'publish-data' --config ~/emhass/config.json
```

Then specify user rights and make the files executables:

```bash
sudo chmod -R 755 ~/emhass/scripts/dayahead_optim.sh
sudo chmod -R 755 ~/emhass/scripts/publish_data.sh
sudo chmod +x ~/emhass/scripts/dayahead_optim.sh
sudo chmod +x ~/emhass/scripts/publish_data.sh
```

### Common for any installation method

#### Options 1, Home Assistant automate publish

In `automations.yaml`:

```yaml
- alias: EMHASS day-ahead optimization
  trigger:
    platform: time
    at: "05:30:00"
  action:
    - service: shell_command.dayahead_optim
- alias: EMHASS publish data
  trigger:
    - minutes: /5
      platform: time_pattern
  action:
    - service: shell_command.publish_data
```

In these automations the day-ahead optimization is performed once a day, every
day at 5:30am, and the data _(output of automation)_ is published every 5
minutes.

#### Option 2, EMHASS automated publish

In `automations.yaml`:

```yaml
- alias: EMHASS day-ahead optimization
  trigger:
    platform: time
    at: "05:30:00"
  action:
    - service: shell_command.dayahead_optim
    - service: shell_command.publish_data
```

in configuration page/`config.json`

```json
"method_ts_round": "first"
"continual_publish": true
```

In this automation, the day-ahead optimization is performed once a day, every
day at 5:30am. If the `optimization_time_step` parameter is set to `30`
_(default)_ in the configuration, the results of the day-ahead optimization will
generate 48 values _(for each entity)_, a value for every 30 minutes in a day
_(i.e. 24 hrs x 2)_.

Setting the parameter `continual_publish` to `true` in the configuration page
will allow EMHASS to store the optimization results as entities/sensors into
separate json files. `continual_publish` will periodically (every
`optimization_time_step` amount of minutes) run a publish, and publish the
optimization results of each generated entities/sensors to Home Assistant. The
current state of the sensor/entity being updated every time publish runs,
selecting one of the 48 stored values, by comparing the stored values'
timestamps, the current timestamp and
[`'method_ts_round': "first"`](#the-publish-data-specificities) to select the
optimal stored value for the current state.

option 1 and 2 are very similar, however, option 2 (`continual_publish`) will
require a CPU thread to constantly be run inside of EMHASS, lowering efficiency.
The reason why you may pick one over the other is explained in more detail below
in [continual_publish](#continual_publish-emhass-automation).

Lastly, we can link an EMHASS published entity/sensor's current state to a Home
Assistant entity on/off switch, controlling a desired controllable load. For
example, imagine that I want to control my water heater. I can use a published
`deferrable` EMHASS entity to control my water heater's desired behavior. In
this case, we could use an automation like the below, to control the desired
water heater on and off:

on:

```yaml
automation:
  - alias: Water Heater Optimized ON
    trigger:
      - minutes: /5
        platform: time_pattern
    condition:
      - condition: numeric_state
        entity_id: sensor.p_deferrable0
        above: 0.1
    action:
      - service: homeassistant.turn_on
        entity_id: switch.water_heater_switch
```

off:

```yaml
automation:
  - alias: Water Heater Optimized OFF
    trigger:
      - minutes: /5
        platform: time_pattern
    condition:
      - condition: numeric_state
        entity_id: sensor.p_deferrable0
        below: 0.1
    action:
      - service: homeassistant.turn_off
        entity_id: switch.water_heater_switch
```

These automations will turn on and off the Home Assistant entity
`switch.water_heater_switch` using the current state from the EMHASS entity
`sensor.p_deferrable0`. `sensor.p_deferrable0` being the entity generated from
the EMHASS day-ahead optimization and published by examples above. The
`sensor.p_deferrable0` entity's current state is updated every 30 minutes (or
`optimization_time_step` minutes) via an automated publish option 1 or 2.
_(selecting one of the 48 stored data values)_

## The publish-data specificities

`publish-data` (which is either run manually or automatically via
`continual_publish` or Home Assistant automation), will push the optimization
results to Home Assistant for each deferrable load defined in the configuration.
For example, if you have defined two deferrable loads, then the command will
publish `sensor.p_deferrable0` and `sensor.p_deferrable1` to Home Assistant.
When the `dayahead-optim` is launched, after the optimization, either entity
json files or a csv file will be saved on disk. The `publish-data` command will
load the latest csv/json files to look for the closest timestamp that matches
the current time using the `datetime.now()` method in Python. This means that if
EMHASS is configured for 30-minute time step optimizations, the csv/json will be
saved with timestamps 00:00, 00:30, 01:00, 01:30, ... and so on. If the current
time is 00:05, and parameter `method_ts_round` is set to `nearest` in the
configuration, then the closest timestamp of the optimization results that will
be published is 00:00. If the current time is 00:25, then the closest timestamp
of the optimization results that will be published is 00:30.

The `publish-data` command will also publish PV and load forecast data on
sensors `p_pv_forecast` and `p_load_forecast`. If using a battery, then the
battery-optimized power and the SOC will be published on sensors
`p_batt_forecast` and `soc_batt_forecast`. On these sensors, the future values
are passed as nested attributes.

If you run publish manually _(or via a Home Assistant Automation)_, it is
possible to provide custom sensor names for all the data exported by the
`publish-data` command. For this, when using the `publish-data` endpoint we can
just add some runtime parameters as dictionaries like this:

```yaml
shell_command:
  publish_data: "curl -i -H \"Content-Type:application/json\" -X POST -d '{\"custom_load_forecast_id\": {\"entity_id\": \"sensor.p_load_forecast\", \"unit_of_measurement\": \"W\", \"friendly_name\": \"Load Power Forecast\"}}' http://localhost:5000/action/publish-data"
```

These keys are available to modify: `custom_pv_forecast_id`,
`custom_load_forecast_id`, `custom_batt_forecast_id`,
`custom_batt_soc_forecast_id`, `custom_grid_forecast_id`, `custom_cost_fun_id`,
`custom_deferrable_forecast_id`, `custom_unit_load_cost_id` and
`custom_unit_prod_price_id`.

If you provide the `custom_deferrable_forecast_id` then the passed data should
be a list of dictionaries, like this:

```yaml
shell_command:
  publish_data: "curl -i -H \"Content-Type:application/json\" -X POST -d '{\"custom_deferrable_forecast_id\": [{\"entity_id\": \"sensor.p_deferrable0\",\"unit_of_measurement\": \"W\", \"friendly_name\": \"Deferrable Load 0\"},{\"entity_id\": \"sensor.p_deferrable1\",\"unit_of_measurement\": \"W\", \"friendly_name\": \"Deferrable Load 1\"}]}' http://localhost:5000/action/publish-data"
```

You should be careful that the list of dictionaries has the correct length,
which is the number of defined deferrable loads.

### Computed variables and published data

Below you can find a list of the variables resulting from EMHASS computation,
shown in the charts and published to Home Assistant through the `publish_data`
command:

| EMHASS variable                      | Definition                                                                                                                                                                                                                                                                                                                                                                                                                                                 | Home Assistant published sensor |
| ------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------- |
| P_PV                                 | Forecasted power generation from your solar panels (Watts). This helps you predict how much solar energy you will produce during the forecast period.                                                                                                                                                                                                                                                                                                      | sensor.p_pv_forecast            |
| P_Load                               | Forecasted household power consumption (Watts). This gives you an idea of how much energy your appliances are expected to use.                                                                                                                                                                                                                                                                                                                             | sensor.p_load_forecast          |
| P_deferrableX<br/>[X = 0, 1, 2, ...] | Forecasted power consumption of deferrable loads (Watts). Deferable loads are appliances that can be managed by EMHASS. EMHASS helps you optimize energy usage by prioritizing solar self-consumption and minimizing reliance on the grid or by taking advantage or supply and feed-in tariff volatility. You can have multiple deferable loads and you use this sensor in HA to control these loads via smart switch or other IoT means at your disposal. | sensor.p_deferrableX            |
| P_grid_pos                           | Forecasted power imported from the grid (Watts). This indicates the amount of energy you are expected to draw from the grid when your solar production is insufficient to meet your needs or it is advantageous to consume from the grid.                                                                                                                                                                                                                  | -                               |
| P_grid_neg                           | Forecasted power exported to the grid (Watts). This indicates the amount of excess solar energy you are expected to send back to the grid during the forecast period.                                                                                                                                                                                                                                                                                      | -                               |
| P_batt                               | Forecasted (dis)charge power load (Watts) for the battery (if installed). If negative it indicates the battery is charging, if positive that the battery is discharging.                                                                                                                                                                                                                                                                                   | sensor.p_batt_forecast          |
| P_grid                               | Forecasted net power flow between your home and the grid (Watts). This is calculated as P_grid_pos + P_grid_neg. A positive value indicates net import, while a negative value indicates net export.                                                                                                                                                                                                                                                       | sensor.p_grid_forecast          |
| SOC_opt                              | Forecasted battery optimized Status Of Charge (SOC) percentage level                                                                                                                                                                                                                                                                                                                                                                                       | sensor.soc_batt_forecast        |
| unit_load_cost                       | Forecasted cost per unit of energy you pay to the grid (typically "Currency"/kWh). This helps you understand the expected energy cost during the forecast period.                                                                                                                                                                                                                                                                                          | sensor.unit_load_cost           |
| unit_prod_price                      | Forecasted price you receive for selling excess solar energy back to the grid (typically "Currency"/kWh). This helps you understand the potential income from your solar production.                                                                                                                                                                                                                                                                       | sensor.unit_prod_price          |
| cost_profit                          | Forecasted profit or loss from your energy usage for the forecast period. This is calculated as unit_load_cost * P_Load - unit_prod_price * P_grid_pos. A positive value indicates a profit, while a negative value indicates a loss.                                                                                                                                                                                                                      | sensor.total_cost_profit_value  |
| cost_fun_cost                        | Forecasted cost associated with deferring loads to maximize solar self-consumption. This helps you evaluate the trade-off between managing the load and not managing and potential cost savings.                                                                                                                                                                                                                                                           | sensor.total_cost_fun_value     |
| optim_status                         | This contains the status of the latest execution and is the same you can see in the Log following an optimization job. Its values can be Optimal or Infeasible.                                                                                                                                                                                                                                                                                            | sensor.optim_status             |

## Passing your own data

In EMHASS we have 4 forecasts to deal with:

- PV power production forecast (internally based on the weather forecast and the
  characteristics of your PV plant). This is given in Watts.

- Load power forecast: how much power your house will demand in the next 24
  hours. This is given in Watts.

- Load cost forecast: the price of the energy from the grid in the next 24
  hours. This is given in EUR/kWh.

- PV production selling price forecast: at what price are you selling your
  excess PV production in the next 24 hours. This is given in EUR/kWh.

The sensor containing the load data should be specified in the parameter
`sensor_power_load_no_var_loads` in the configuration file. As we want to
optimize household energy, we need to forecast the load power consumption. The
default method for this is a naive approach using 1-day persistence. The load
data variable should not contain the data from the deferrable loads themselves.
For example, let's say that you set your deferrable load to be the washing
machine. The variables that you should enter in EMHASS will be:
`sensor_power_load_no_var_loads: 'sensor.power_load_no_var_loads'` and
`sensor.power_load_no_var_loads = sensor.power_load - sensor.power_washing_machine`.
This is supposing that the overall load of your house is contained in the
variable: `sensor.power_load`. The sensor `sensor.power_load_no_var_loads` can
be easily created with a new template sensor in Home Assistant.

If you are implementing an MPC controller, then you should also need to provide
some data at the optimization runtime using the key `runtimeparams`.

The valid values to pass for both forecast data and MPC-related data are
explained below.

### Alternative publish methods

Due to the flexibility of EMHASS, multiple different approaches to publishing
the optimization results have been created. Select an option that best meets
your use case:

#### publish last optimization _(manual)_

By default, running an optimization in EMHASS will output the results into the
CSV file: `data_path/opt_res_latest.csv` _(overriding the existing data on that
file)_. We run the publish command to publish the last optimization saved in the
`opt_res_latest.csv`:

```bash
# RUN dayahead
curl -i -H 'Content-Type:application/json' -X POST -d {} http://localhost:5000/action/dayahead-optim
# Then publish teh results of dayahead
curl -i -H 'Content-Type:application/json' -X POST -d {} http://localhost:5000/action/publish-data
```

_Note, the published entities from the publish-data action will not
automatically update the entities' current state (current state being used to
check when to turn on and off appliances via Home Assistant automations). To
update the EMHASS entities state, another publish would have to be re-run later
when the current time matches the next value's timestamp (e.g. every 30
minutes). See examples below for methods to automate the publish-action._

#### continual_publish _(EMHASS Automation)_

As discussed in
[Common for any installation method - option 2](#option-2-emhass-automate-publish),
setting `continual_publish` to `true` in the configuration saves the output of
the optimization into the `data_path/entities` folder _(a .json file for each
sensor/entity)_. A constant loop (in `optimization_time_step` minutes) will run,
observe the .json files in that folder, and publish the saved files periodically
(updating the current state of the entity by comparing date.now with the saved
data value timestamps).

For users that wish to run multiple different optimizations, you can set the
runtime parameter: `publish_prefix` to something like: `"mpc_"` or `"dh_"`. This
will generate unique entity_id names per optimization and save these unique
entities as separate files in the folder. All the entity files will then be
updated when the next loop iteration runs. If a different
`optimization_time_step` integer was passed as a runtime parameter in an
optimization, the `continual_publish` loop will be based on the lowest
`optimization_time_step` saved. An example:

```bash
# RUN dayahead, with optimization_time_step=30 (default), prefix=dh_ 
curl -i -H 'Content-Type:application/json' -X POST -d '{"publish_prefix":"dh_"}' http://localhost:5000/action/dayahead-optim
# RUN MPC, with optimization_time_step=5, prefix=mpc_
curl -i -H 'Content-Type:application/json' -X POST -d '{'optimization_time_step':5,"publish_prefix":"mpc_"}' http://localhost:5000/action/naive-mpc-optim
```

This will tell continual_publish to loop every 5 minutes based on the
optimization_time_step passed in MPC. All entities from the output of dayahead
"dh_" and MPC "mpc_" will be published every 5 minutes.

</br>

_It is recommended to use the 2 other options below once you have a more
advanced understanding of EMHASS and/or Home Assistant._

#### Mixture of continual_publish and manual _(Home Assistant Automation for Publish)_

You can choose to save one optimization for continual_publish and bypass another
optimization by setting `'continual_publish':false` runtime parameter:

```bash
# RUN dayahead, with optimization_time_step=30 (default), prefix=dh_, included into continual_publish
curl -i -H 'Content-Type:application/json' -X POST -d '{"publish_prefix":"dh_"}' http://localhost:5000/action/dayahead-optim

# RUN MPC, with optimization_time_step=5, prefix=mpc_, Manually publish, excluded from continual_publish loop
curl -i -H 'Content-Type:application/json' -X POST -d '{'continual_publish':false,'optimization_time_step':5,"publish_prefix":"mpc_"}' http://localhost:5000/action/naive-mpc-optim
# Publish MPC output
curl -i -H 'Content-Type:application/json' -X POST -d {} http://localhost:5000/action/publish-data
```

This example saves the dayahead optimization into `data_path/entities` as .json
files, being included in the `continutal_publish` loop (publishing every 30
minutes). The MPC optimization will not be saved in `data_path/entities`, and
therefore only into `data_path/opt_res_latest.csv`. Requiring a publish-data
action to be run manually (or via a Home Assistant) Automation for the MPC
results.

#### Manual _(Home Assistant Automation for Publish)_

For users who wish to have full control of exactly when they would like to run a
publish and have the ability to save multiple different optimizations. The
`entity_save` runtime parameter has been created to save the optimization output
entities to .json files whilst `continual_publish` is set to `false` in the
configuration. Allowing the user to reference the saved .json files manually via
a publish:

in configuration page/`config.json` :

```json
"continual_publish": false
```

POST action :

```bash
# RUN dayahead, with optimization_time_step=30 (default), prefix=dh_, save entity
curl -i -H 'Content-Type:application/json' -X POST -d '{"entity_save": true, "publish_prefix":"dh_"}' http://localhost:5000/action/dayahead-optim
# RUN MPC, with optimization_time_step=5, prefix=mpc_, save entity
curl -i -H 'Content-Type:application/json' -X POST -d '{"entity_save": true", 'optimization_time_step':5,"publish_prefix":"mpc_"}' http://localhost:5000/action/naive-mpc-optim
```

You can then reference these .json saved entities via their `publish_prefix`.
Include the same `publish_prefix` in the `publish_data` action:

```bash
#Publish the MPC optimization ran above 
curl -i -H 'Content-Type:application/json' -X POST -d '{"publish_prefix":"mpc_"}'  http://localhost:5000/action/publish-data
```

This will publish all entities from the MPC (_mpc) optimization above.
</br> Alternatively, you can choose to publish all the saved files .json files
with `publish_prefix` = all:

```bash
#Publish all saved entities
curl -i -H 'Content-Type:application/json' -X POST -d '{"publish_prefix":"all"}'  http://localhost:5000/action/publish-data
```

This action will publish the dayahead (_dh) and MPC (_mpc) optimization results
from the optimizations above.

### Forecast data at runtime

It is possible to provide EMHASS with your own forecast data. For this just add
the data as a list of values to a data dictionary during the call to `emhass`
using the `runtimeparams` option.

For example, if using the add-on or the standalone docker installation you can
pass this data as a list of values to the data dictionary during the `curl`
POST:

```bash
curl -i -H 'Content-Type:application/json' -X POST -d '{"pv_power_forecast":[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 70, 141.22, 246.18, 513.5, 753.27, 1049.89, 1797.93, 1697.3, 3078.93, 1164.33, 1046.68, 1559.1, 2091.26, 1556.76, 1166.73, 1516.63, 1391.13, 1720.13, 820.75, 804.41, 251.63, 79.25, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]}' http://localhost:5000/action/dayahead-optim
```

Or if using the legacy method using a Python virtual environment:

```bash
emhass --action 'dayahead-optim' --config ~/emhass/config.json --runtimeparams '{"pv_power_forecast":[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 70, 141.22, 246.18, 513.5, 753.27, 1049.89, 1797.93, 1697.3, 3078.93, 1164.33, 1046.68, 1559.1, 2091.26, 1556.76, 1166.73, 1516.63, 1391.13, 1720.13, 820.75, 804.41, 251.63, 79.25, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]}'
```

The possible dictionary keys to pass data are:

- `pv_power_forecast` for the PV power production forecast.

- `load_power_forecast` for the Load power forecast.

- `load_cost_forecast` for the Load cost forecast.

- `prod_price_forecast` for the PV production selling price forecast.

### Passing other data at runtime

It is possible to also pass other data during runtime to automate energy
management. For example, it could be useful to dynamically update the total
number of hours for each deferrable load
(`operating_hours_of_each_deferrable_load`) using for instance a correlation
with the outdoor temperature (useful for water heater for example).

Here is the list of the other additional dictionary keys that can be passed at
runtime:

- `number_of_deferrable_loads` for the number of deferrable loads to consider.

- `nominal_power_of_deferrable_loads` for the nominal power for each deferrable
  load in Watts.

- `operating_hours_of_each_deferrable_load` for the total number of hours that
  each deferrable load should operate.
  - Alteratively, you can pass `operating_timesteps_of_each_deferrable_load` to
    set the total number of timesteps for each deferrable load. _(better
    parameter to use for setting under 1 hr)_

- `start_timesteps_of_each_deferrable_load` for the timestep from which each
  deferrable load is allowed to operate (if you don't want the deferrable load
  to use the whole optimization timewindow).

- `end_timesteps_of_each_deferrable_load` for the timestep before which each
  deferrable load should operate (if you don't want the deferrable load to use
  the whole optimization timewindow).

- `def_current_state` Pass this as a list of booleans (True/False) to indicate
  the current deferrable load state. This is used internally to avoid
  incorrectly penalizing a deferrable load start if a forecast is run when that
  load is already running.

- `treat_deferrable_load_as_semi_cont` to define if we should treat each
  deferrable load as a semi-continuous variable.

- `set_deferrable_load_single_constant` to define if we should set each
  deferrable load as a constant fixed value variable with just one startup for
  each optimization task.

- `solcast_api_key` for the SolCast API key if you want to use this service for
  PV power production forecast.

- `solcast_rooftop_id` for the ID of your rooftop for the SolCast service
  implementation.

- `solar_forecast_kwp` for the PV peak installed power in kW used for the
  solar.forecast API call.

- `battery_minimum_state_of_charge` the minimum possible SOC.

- `battery_maximum_state_of_charge` the maximum possible SOC.

- `battery_target_state_of_charge` for the desired target value of the initial
  and final SOC.

- `battery_discharge_power_max` for the maximum battery discharge power.

- `battery_charge_power_max` for the maximum battery charge power.

- `publish_prefix` use this key to pass a common prefix to all published data.
  This will add a prefix to the sensor name but also the forecast attribute keys
  within the sensor.

## A naive Model Predictive Controller

An MPC controller was introduced in v0.3.0. This is an informal/naive
representation of an MPC controller. This can be used in combination with/as a
replacement for the Dayahead Optimization.

An MPC controller performs the following actions:

- Set the prediction horizon and receding horizon parameters.
- Perform an optimization on the prediction horizon.
- Apply the first element of the obtained optimized control variables.
- Repeat at a relatively high frequency, ex: 5 min.

This is the receding horizon principle.

When applying this controller, the following `runtimeparams` should be defined:

- `prediction_horizon` for the MPC prediction horizon. Fix this at least 5 times
  the optimization time step.

- `soc_init` for the initial value of the battery SOC for the current iteration
  of the MPC.

- `soc_final` for the final value of the battery SOC for the current iteration
  of the MPC.

- `operating_hours_of_each_deferrable_load` for the list of deferrable loads
  functioning hours. These values can decrease as the day advances to take into
  account receding horizon daily energy objectives for each deferrable load.

- `start_timesteps_of_each_deferrable_load` for the timestep from which each
  deferrable load is allowed to operate (if you don't want the deferrable load
  to use the whole optimization timewindow). If you specify a value of 0 (or
  negative), the deferrable load will be optimized as from the beginning of the
  complete prediction horizon window.

- `end_timesteps_of_each_deferrable_load` for the timestep before which each
  deferrable load should operate (if you don't want the deferrable load to use
  the whole optimization timewindow). If you specify a value of 0 (or negative),
  the deferrable load optimization window will extend up to the end of the
  prediction horizon window.

A correct call for an MPC optimization should look like this:

```bash
curl -i -H 'Content-Type:application/json' -X POST -d '{"pv_power_forecast":[0, 70, 141.22, 246.18, 513.5, 753.27, 1049.89, 1797.93, 1697.3, 3078.93], "prediction_horizon":10, "soc_init":0.5,"soc_final":0.6}' http://192.168.3.159:5000/action/naive-mpc-optim
```

_Example with :`operating_hours_of_each_deferrable_load`,
`start_timesteps_of_each_deferrable_load`,
`end_timesteps_of_each_deferrable_load`._

```bash
curl -i -H 'Content-Type:application/json' -X POST -d '{"pv_power_forecast":[0, 70, 141.22, 246.18, 513.5, 753.27, 1049.89, 1797.93, 1697.3, 3078.93], "prediction_horizon":10, "soc_init":0.5,"soc_final":0.6,"operating_hours_of_each_deferrable_load":[1,3],"start_timesteps_of_each_deferrable_load":[0,3],"end_timesteps_of_each_deferrable_load":[0,6]}' http://localhost:5000/action/naive-mpc-optim
```

For a more readable option we can use the `rest_command` integration:

```yaml
rest_command:
  url: http://127.0.0.1:5000/action/dayahead-optim
  method: POST
  headers:
    content-type: application/json
  payload: >-
    {
      "pv_power_forecast": [0, 70, 141.22, 246.18, 513.5, 753.27, 1049.89, 1797.93, 1697.3, 3078.93],
      "prediction_horizon":10,
      "soc_init":0.5,
      "soc_final":0.6,
      "operating_hours_of_each_deferrable_load":[1,3],
      "start_timesteps_of_each_deferrable_load":[0,3],
      "end_timesteps_of_each_deferrable_load":[0,6]
    }
```

## A machine learning forecaster

Starting in v0.4.0 a new machine learning forecaster class was introduced. This
is intended to provide a new and alternative method to forecast your household
consumption and use it when such forecast is needed to optimize your energy
through the available strategies. Check the dedicated section in the
documentation here:
[https://emhass.readthedocs.io/en/latest/mlforecaster.html](https://emhass.readthedocs.io/en/latest/mlforecaster.html)

## Development

Pull requests are very much accepted on this project. For development, you can
find some instructions here
[Development](https://emhass.readthedocs.io/en/latest/develop.html).

## Troubleshooting

Some problems may arise from solver-related issues in the Pulp package. It was
found that for arm64 architectures (ie. Raspberry Pi4, 64 bits) the default
solver is not available. A workaround is to use another solver. The `glpk`
solver is an option.

This can be controlled in the configuration file with parameters `lp_solver` and
`lp_solver_path`. The options for `lp_solver` are: 'PULP_CBC_CMD', 'GLPK_CMD',
'HiGHS', and 'COIN_CMD'. If using 'COIN_CMD' as the solver you will need to
provide the correct path to this solver in parameter `lp_solver_path`, ex:
'/usr/bin/cbc'.

## License

MIT License

Copyright (c) 2021-2025 David HERNANDEZ

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

```
```

# smartthings_customize

Made based on SmartThings component, an integrated component of HomeAssistant

Component for adding functionality not supported in the official SmartThings component


# installation

step1. You can add it by registering it as a custom repository in HACS, or by downloading the code

step2. Restart HomeAssistant and install the SmartThings Customize component. The installation process is identical to the official SmartThings component

step3. After installing "config/smartthings_customize/{locationName}.yaml" Check if the file was created.

step4. Please write the generated yaml file by referring to the example below.

# example

- Name creation rules, You can use label, component, capability, attribute, and command items.
Please refer to the button example in example.<br><br>
  "%{label}%{component}%{capability}%{attribute}%{command} fan power"

- Rules can also be applied to entity ids.<br>Check default_entity_id_format: "st_custom_%{device_id}_%{label}_%{component}_%{capability}_%{attribute}_%{command}_%{name}"<br><br>
And in each capability setting It can be set with entity_id_format:<br><br>
example) entity_id_format: st_custom_%{device_id}_%{device_type}_%{label}_%{component}_%{capability}_%{attribute}_%{command}_%{name}

<br><br>
```
# https://my.smartthings.com/advanced/
# After identifying the information of the device from the above site, modify the setting file

globals:
  ignore_capabilities:
    # - healthCheck
    # - accelerationSensor
    # - activityLightingMode
    # - airConditionerFanMode
    # - airConditionerMode
    # - airFlowDirection
    # - airQualitySensor
    # - alarm
    # - audioMute
    # - audioVolume
    # - battery
    # - bodyMassIndexMeasurement
    # - bodyWeightMeasurement
    # - button
    # - carbonDioxideMeasurement
    # - carbonMonoxideDetector
    # - carbonMonoxideMeasurement
    # - colorControl
    # - colorTemperature
    # - contactSensor
    # - demandResponseLoadControl
    # - dishwasherMode
    # - dishwasherOperatingState
    # - doorControl
    # - dryerMode
    # - dryerOperatingState
    # - dustSensor
    # - energyMeter
    # - equivalentCarbonDioxideMeasurement
    # - execute
    # - fanSpeed
    # - filterStatus
    # - formaldehydeMeasurement
    # - garageDoorControl
    # - gasMeter
    # - illuminanceMeasurement
    # - infraredLevel
    # - lock
    # - mediaInputSource
    # - mediaPlayback
    # - mediaPlaybackRepeat
    # - mediaPlaybackShuffle
    # - motionSensor
    # - ocf
    # - odorSensor
    # - ovenMode
    # - ovenOperatingState
    # - ovenSetpoint
    # - powerConsumptionReport
    # - powerMeter
    # - powerSource
    # - presenceSensor
    # - rapidCooling
    # - refrigerationSetpoint
    # - relativeHumidityMeasurement
    # - robotCleanerCleaningMode
    # - robotCleanerMovement
    # - robotCleanerTurboMode
    # - signalStrength
    # - smokeDetector
    # - soundSensor
    # - switch
    # - switchLevel
    # - tamperAlert
    # - temperatureMeasurement
    # - thermostat
    # - thermostatCoolingSetpoint
    # - thermostatFanMode
    # - thermostatHeatingSetpoint
    # - thermostatMode
    # - thermostatOperatingState
    # - thermostatSetpoint
    # - threeAxis
    # - tvChannel
    # - tvocMeasurement
    # - ultravioletIndex
    # - valve
    # - voltageMeasurement
    # - washerMode
    # - washerOperatingState
    # - waterSensor
    # - windowShade


  lock:
    - name: "door lock"
      component: main
      capability: switch
      state:
        attribute: switch
      command:
        "lock": "on"
        "unlock": "off"
      lock_state: ["on"]
      
  switch:
    - name: "power cool"
      capability: refrigeration
      component: main
      command:
        "on": "setRapidCooling"
        "off": "setRapidCooling"
      argument:
        "on": ["on"]
        "off": ["off"]
        #type: optional
      state:
        #component: optional
        #capability: optional
        attribute: rapidCooling
      on_state: ["on"]

    - name: "power freeze"
      capability: refrigeration
      component: main
      command:
        "on": "setRapidFreezing"
        "off": "setRapidFreezing"
      argument:
        "on": ["on"]
        "off": ["off"]
        #type: optional
      state:
        attribute: rapidFreezing
      on_state: ["on"]

  sensor:
    - name: power cool activate
      capability: refrigeration
      component: main
      state:
        attribute: rapidCooling
      default_unit:
      device_class:
      state_class:
      entity_category:

    - name: power freeze activate
      capability: refrigeration
      component: main
      state:
        attribute: rapidFreezing
      default_unit:
      device_class:
      state_class:
      entity_category:

  binary_sensor:
    - name: rapid cooling
      capability: refrigeration
      component: main
      state:
        attribute: rapidCooling
      on_state: ["on"]
      device_class:
      entity_category:

    - name: rapid freezing
      capability: refrigeration
      component: main
      state:
        attribute: rapidFreezing
      on_state: ["on"]

  select:
    - name: "operating"
      component: main
      capability: samsungce.robotCleanerOperatingState
      options:
        attribute: supportedOperatingState
      command: setOperatingState
      state:
        attribute: operatingState

  number:
    - name: "set freezer temperature"
      capability: thermostatCoolingSetpoint
      component: freezer
      command: setCoolingSetpoint
      state:
        attribute: coolingSetpoint
      mode: slider
      #min: -23
      min:
        component: freezer
        capability: custom.thermostatSetpointControl
        attribute: minimumSetpoint
      max: -17
      step: 1
      parent_entity_id: binary_sensor.naengjanggo_contact_2

  # Enter the information of the button entity to be added.
  # You must enter the command entry for your SmartThings device and specify the properties that are changed by the
  # Galaxy home mini ir fan example
  button:
    - name: "%{label} %{component} %{capability} %{attribute} %{command} fan power"
      capability: statelessPowerToggleButton
      component: main
      command: setButton
      argument: [powerToggle]

    - name: "fan speed"
      capability: statelessFanspeedButton
      component: main
      command: setButton
      argument: [fanspeedUp]

  text:
    - name: "Input Source"
      capability: samsungvd.mediaInputSource
      component: "main"
      command: setInputSource
      state:
        attribute: inputSource

    - name: "명령"
      capability: samsungim.bixbyContent
      component: main
      command: bixbyCommand
      state:
        attribute: text

    - name: "방송"
      capability: speechSynthesis
      component: main
      command: speak
      state:
        attribute: text

  # The device ID of the SmartThings to ignore. Once added here, it will not be added as a device.
  # This setting does not affect individual device settings (devies:)
  ignore_devices: []
  #  - b065a858-1927-fd98-a374-7fc1498e8c76

# You can also add settings for individual devices under the devices: entry
# (if you add them here they will be ignored in the global settings).
# parent_entity_id - Included in the same device as the specified entity ID
devices:
  # kimchi refrigerator example
  - device_id: bc98a847-3fbb-e0fa-96f9-e9a8157c16ae
    binary_sensor:
      - name: top contact
        capability: contactSensor
        component: top
        state:
          attribute: contact
        on_state: ["open"]
        device_class: door
      - name: middle contact
        capability: contactSensor
        component: middle
        state:
          attribute: contact
        on_state: ["open"]
        device_class: door
      - name: bottom contact
        capability: contactSensor
        component: bottom
        state:
          attribute: contact
        on_state: ["open"]
        device_class: door

    sensor:
      - name: top OperatingState
        capability: samsungce.kimchiRefrigeratorOperatingState
        component: top
        state:
          attribute: operatingState
          key: mode
  # vacuum example
  - device_id: "46955634-09e8-6bc7-0167-a73b2e9182e6"
    vacuum:
      - name: "robot vacuum test"
        component: main
        capability: samsungce.robotCleanerOperatingState
        capabilities:
          - commands:
            capability: samsungce.robotCleanerOperatingState
            command: setOperatingState
            argument:
              "return": ["homing"]
              "start": ["cleaning"]
              "stop": ["paused"]
            state:
              attribute: operatingState
            s2h_state_mapping:
              [
                {
                  "charging": "docked",
                  "charged": "docked",
                  "returning": "homing",
                },
              ]
          - fan_speed:
            capability: robotCleanerTurboMode
            options: ["on", "off"]
            command: setRobotCleanerTurboMode
            s2h_fan_speed_mapping: [{ "on": "turbo", "off": "normal" }]
            state:
              attribute: robotCleanerTurboMode

  - device_id: b065a858-1927-fd98-a374-7fc1498e8c76
    type: ocf
    sensor:
      - name: power cool activate
        capability: refrigeration
        component: main
        state:
          attribute: rapidCooling
        default_unit:
        device_class:
        state_class:
        entity_category:

      - name: power freeze activate
        capability: refrigeration
        component: main
        state:
          attribute: rapidFreezing
        default_unit:
        device_class:
        state_class:
        entity_category:

    switch:
      - name: "power cool"
        capability: refrigeration
        component: main
        command:
          "on": "setRapidCooling"
          "off": "setRapidCooling"
        argument:
          "on": ["on"]
          "off": ["off"]
        state:
          attribute: rapidCooling
        on_state: ["on"]

      - name: "power freeze"
        capability: refrigeration
        component: main
        command:
          "on": "setRapidFreezing"
          "off": "setRapidFreezing"
        argument:
          "on": ["on"]
          "off": ["off"]
        state:
          attribute: rapidFreezing
        on_state: ["on"]
    climate:
      - name: freezer temperature
        capability: thermostatCoolingSetpoint
        component: freezer
        capabilities:
          - switch:
            capability: refrigeration
            component: main
            command:
              "on": "setRapidCooling"
              "off": "setRapidCooling"
            argument:
              "on": ["on"]
              "off": ["off"]
            state:
              attribute: rapidCooling
          - mode:
            capability: refrigeration
            component: main
            command: setRapidCooling
            state:
              attribute: rapidCooling
            options: ["cool", "off"]
            s2h_mode_mapping: [{ "on": "cool" }]
            s2h_action_mapping: [{ "on": "cooling", "off": "off" }]

          - target_temp:
            apply_mode: "cool"
            capability: thermostatCoolingSetpoint
            min:
              capability: custom.thermostatSetpointControl
              attribute: minimumSetpoint
            max:
              capability: custom.thermostatSetpointControl
              attribute: maximumSetpoint
            step: 1
            command: setCoolingSetpoint
            state:
              attribute: coolingSetpoint
            argument:
              type: float
          - target_temp:
            apply_mode: "off"
            capability: thermostatCoolingSetpoint
            min:
              capability: custom.thermostatSetpointControl
              attribute: minimumSetpoint
            max:
              capability: custom.thermostatSetpointControl
              attribute: maximumSetpoint
            step: 1
            command: setCoolingSetpoint
            state:
              attribute: coolingSetpoint
            argument:
              type: float
          - current_temperature:
            capability: temperatureMeasurement
            state:
              attribute: temperature

  - device_id: 53eade61-7950-4b89-868b-60ee53e49248
    fan:
      - name: "fan test"
        capability: airConditionerFanMode
        component: main
        capabilities:
          - switch:
            capability: switch
            component: main
            command:
              "on": "on"
              "off": "off"
            argument:
              "on": []
              "off": []
          - preset_mode:
            capability: airConditionerFanMode
            options:
              attribute: supportedAcModes
            command: setFanMode
            state:
              attribute: fanMode
          - direction:
            capability: airConditionerFanMode
            options:
              attribute: supportedAcModes
            command: setFanMode
            state:
              attribute: fanMode
            oscillate_modes: ["low"]
          - percentage:
            capability: thermostatCoolingSetpoint
            min: 0
            max: 100
            step: 1
            command: setCoolingSetpoint
            state:
              attribute: coolingSetpoint
    climate:
      - name: "Bedroom Aircon"
        capability: airConditionerMode
        component: main
        capabilities:
          - switch:
            capability: switch
            component: main
            command:
              "on": "on"
              "off": "off"
            state:
              attribute: switch
            argument:
              "on": []
              "off": []
          - mode:
            capability: airConditionerMode
            options:
              ["off", "wind", "cool", "dry"]
              #attribute: supportedAcModes
            command: setAirConditionerMode
            state:
              attribute: airConditionerMode
            s2h_mode_mapping: [{ "wind": "fan_only" }]
            s2h_action_mapping:
              [{ "cool": "cooling", "dry": "drying", "off": "off" }]
          - fan_mode:
            capability: airConditionerFanMode
            options:
              attribute: supportedAcFanModes
            command: setFanMode
            state:
              attribute: fanMode
            s2h_fan_mode_mapping: [{}]
          - preset_mode:
            capability: airConditionerFanMode
            options:
              attribute: supportedAcFanModes
            command: setFanMode
            state:
              attribute: fanMode

          - swing_mode:
            capability: airConditionerFanMode
            options:
              attribute: supportedAcFanModes
            command: setFanMode
            state:
              attribute: fanMode

          - target_temp:
            capability: thermostatCoolingSetpoint
            min: 22
            max: 28
            step: 1
            command: setCoolingSetpoint
            state:
              attribute: coolingSetpoint

          - target_temp_low:
            capability: thermostatCoolingSetpoint
            command: setCoolingSetpoint
            state:
              attribute: coolingSetpoint

          - target_temp_high:
            capability: thermostatCoolingSetpoint
            command: setCoolingSetpoint
            state:
              attribute: coolingSetpoint

          - target_humidity:
            capability: thermostatCoolingSetpoint
            min: 40
            max: 60
            step: 1
            command: setCoolingSetpoint
            state:
              attribute: coolingSetpoint

          - current_temperature:
            capability: temperatureMeasurement
            state:
              attribute: temperature
          - current_humidity:
            entity_id: input_number.hum

          - aux_heat:
            capability: airConditionerMode
            state:
              attribute: airConditionerMode
            aux_heat_modes: ["cool", "dry"]

ignore_platforms:
  - scene

default_entity_id_format: "st_custom_%{device_id}_%{device_type}_%{label}_%{component}_%{capability}_%{attribute}_%{command}_%{name}"


  ```


# support entity

- number
- switch
- sensor
- binary_sensor
- select
- button
- text
- climate
- fan
- lock 
- vacuum
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
example) entity_id_format: st_custom_%{device_id}_%{label}_%{component}_%{capability}_%{attribute}_

<br><br>
```
# https://my.smartthings.com/advanced/
# After identifying the information of the device from the above site, modify the setting file

# Ability to activate features of official integrated components
enable_default_entities: true

globals:
  # Enter the information of the binary sensor to be added. Enter the attributes of your SmartThings device.
  binary_sensors:
    - capability: contactSensor
      component: cooler
      attributes:
        - attribute: contact
          name: cooler contact

  # Enter the information of the sensor to be added. Enter the attributes of your SmartThings device.
  # Empty items can be left blank
  sensors:
    - capability: refrigeration
      component: main
      attributes:
        - attribute: rapidCooling
          name: power cool activate
          default_unit:
          device_class:
          state_class:
          entity_category:
        - attribute: rapidFreezing
          name: power freeze activate
          default_unit:
          device_class:
          state_class:
          entity_category:
    - capability: contactSensor
      component: cooler
      attributes:
        - attribute: contact
          name: cooler contact
          default_unit:
          device_class:
          state_class:
          entity_category:

  # Enter the switch information to be added. You must enter the Command item of the SmartThings device and designate the attribute that is changed by the command.
  # on_state requires a state value that is treated as an on state.
  switches:
    - capability: switch
      component: main
      commands:
        - name: "power"
          on_command: "on"
          off_command: "off"
          argument:
            "on": ["on"]
            "off": ["off"]
          attribute: switch
          on_state: ["on"]

    - capability: refrigeration
      component: main
      commands:
        - name: "power cool"
          on_command: setRapidCooling
          off_command: setRapidCooling
          argument:
            "on": ["on"]
            "off": ["off"]
          attribute: rapidCooling
          on_state: ["on"]
        - name: "power freeze"
          on_command: setRapidCooling
          off_command: setRapidCooling
          argument:
            "on": ["on"]
            "off": ["off"]
          attribute: rapidFreezing
          on_state: ["on"]

  # Enter the information of the number item to be added.
  # You must enter the command entry for your SmartThings device and specify the properties that are changed by the command.
  # For min and max, integers can be specified, or attribute items can be specified.
  numbers:
    - capability: thermostatCoolingSetpoint
      component: freezer
      mode: slider
      min:
        attribute: minimumSetpoint
      max: -17
      step: 1
      commands:
        - name: "set freezer temperature"
          command: setCoolingSetpoint
          attribute: coolingSetpoint

  # Enter the information of the select item to be added. You must enter the command entry for your SmartThings device and specify the properties that are changed by the command.
  selects:
    - capability: airConditionerFanMode
      component: main
      options:
        attribute: supportedAcFanModes
      commands:
        - name: "set fan mode"
          command: setFanMode
          attribute: fanMode
    - capability: airConditionerMode
      component: main
      options:
        attribute: supportedAcModes
      commands:
        - name: "set ac mode"
          command: setAirConditionerMode
          attribute: airConditionerMode

  # Enter the information of the button entity to be added.
  # You must enter the command entry for your SmartThings device and specify the properties that are changed by the
  # Galaxy home mini ir fan example
  buttons:
    - capability: statelessPowerToggleButton
      component: main
      commands:
        - name: "%{label} %{component} %{capability} %{attribute} %{command} fan power"
          command: setButton
          argument: [powerToggle]

    - capability: statelessFanspeedButton
      component: main
      commands:
        - name: "fan speed"
          command: setButton
          argument: [fanspeedUp]

    # An example of changing the quick freezing of the refrigerator to a button
    - capability: refrigeration
      component: main
      commands:
        - name: "power cool button"
          command: setRapidCooling
          argument: ["on"]

  texts:
    - capability: samsungvd.mediaInputSource
      component: "main"
      commands:
        - name: "Input Source"
          command: setInputSource
          attribute: inputSource
    - capability: samsungim.bixbyContent
      component: main
      commands:
        - name: "명령"
          command: bixbyCommand
          attribute: text
    - capability: speechSynthesis
      component: main
      commands:
        - name: "방송"
          command: speak
          attribute: text

  # The device ID of the SmartThings to ignore. Once added here, it will not be added as a device.
  # This setting does not affect individual device settings (devies:)
  ignore_devices:
    - b065a858-1927-fd98-a374-7fc1498e8c76
    - 46955634-09e8-6bc7-0167-a73b2e9182e6

  ignore_capabilities:
    - execute
    - healthCheck
    - ocf

# You can also add settings for individual devices under the devices: entry
# (if you add them here they will be ignored in the global settings).
# parent_entity_id - Included in the same device as the specified entity ID
devices:
  - device_id: "46955634-09e8-6bc7-0167-a73b2e9182e6"
    binary_sensors:
      - component: cooler
        capability: contactSensor
        attributes:
          - attribute: contact
            name: cooler contact
            parent_entity_id: parent_entity_id


# Fill in the appropriate capabilities
# This is a climate example. Fill in the appropriate capability. If you do not use the entity_id  
# attribute, the switch capability is not required.
# For climates->capability, enter mode capability
# Use hvac_modes: to map HomeAssistant's Climate and SmartThings' modes.
    climates:
      - capability: airConditionerMode
        component: main
        attributes:
          - name: "Bedroom Aircon"
            capabilities:
              - switch: switch
              - mode: airConditionerMode
                options:
                  attribute: supportedAcModes
                commands:
                  command: setAirConditionerMode
                  attribute: airConditionerMode
                hvac_modes: [{ "wind": "fan_only" }]
                hvac_actions:
                  [{ "cool": "cooling", "dry": "drying", "off": "off" }]
                aux_heat_modes: ["auxheatonly", "auxiliaryemergencyheat"]

              - fan_mode: airConditionerFanMode
                options:
                  attribute: supportedAcFanModes
                commands:
                  command: setFanMode
                  attribute: fanMode

              - preset_mode: airConditionerFanMode
                options:
                  attribute: supportedAcFanModes
                commands:
                  command: setFanMode
                  attribute: fanMode

              - swing_mode: airConditionerFanMode
                options:
                  attribute: supportedAcFanModes
                commands:
                  command: setFanMode
                  attribute: fanMode

              - target_temp: thermostatCoolingSetpoint
                min: 22
                max: 28
                step: 1
                commands:
                  command: setCoolingSetpoint
                  attribute: coolingSetpoint

              - target_temp_low: thermostatCoolingSetpoint
                commands:
                  command: setCoolingSetpoint
                  attribute: coolingSetpoint

              - target_temp_high: thermostatCoolingSetpoint
                commands:
                  command: setCoolingSetpoint
                  attribute: coolingSetpoint

              - target_humidity: thermostatCoolingSetpoint
                min: 40
                max: 60
                step: 1
                commands:
                  command: setCoolingSetpoint
                  attribute: coolingSetpoint

              - current_temperature: temperatureMeasurement
                attributes:
                  attribute: temperature
              - current_humidity:
                entity_id: input_number.hum

# Fill in the appropriate capabilities
# This is a fan example. Fill in the appropriate capability. If you do not use the entity_id  
# attribute, the switch capability is not required.
    fans:
      - capability: switch
        component: main
        attributes:
          - name: "fan test"
            capabilities:
              - preset_mode: fanOscillationMode
                options:
                  attribute: supportedFanOscillationModes
                commands:
                  command: setFanOscillationMode
                  attribute: fanOscillationMode
              - direction: fanOscillationMode
                options:
                  attribute: supportedFanOscillationModes
                commands:
                  command: setFanOscillationMode
                  attribute: fanOscillationMode
                oscillate_modes: ['vertical', 'horizontal']
              - percent: fanSpeed
                min: 0
                max: 100
                step: 1
                commands:
                  command: setFanSpeed
                  attribute: fanSpeed

ignore_platforms:
  - scene

enable_syntax_property: false

default_entity_id_format: "st_custom_%{device_id}_%{label}_%{component}_%{capability}_%{attribute}_%{command}_%{name}"


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
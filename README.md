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

```
# https://my.smartthings.com/advanced/
# After identifying the information of the device from the above site, modify the setting file

# Ability to activate features of official integrated components
enable_default_entities: false

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
  on_state requires a state value that is treated as an on state.
  switches:
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
        - name: "%{label}%{component}%{capability}%{attribute}%{command} fan power"
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
      

  # The device ID of the SmartThings to ignore. Once added here, it will not be added as a device.
  # This setting does not affect individual device settings (devies:)
  ignore_devices:
    - b065a858-1927-fd98-a374-7fc1498e8c76
    - 46955634-09e8-6bc7-0167-a73b2e9182e6

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

ignore_platforms:
  - scene

  ```




# support entity

- number
- switch
- sensor
- binary_sensor
- select
- button

# smartthings_customize

Made based on SmartThings component, an integrated component of HomeAssistant

Component for adding functionality not supported in the official SmartThings component


# installation

step1. You can add it by registering it as a custom repository in HACS, or by downloading the code

step2. Restart HomeAssistant and install the SmartThings Customize component. The installation process is identical to the official SmartThings component

step3. After installing "config/smartthings customize/settings.yaml" Check if the file was created. If not created you can also add it manually


# example

```
# https://my.smartthings.com/advanced/
# After identifying the information of the device from the above site, modify the setting file

# Ability to activate features of official integrated components
enable_official_component: false

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

# Enter the information of the number item to be added. You must enter the command entry for your SmartThings device and specify the properties that are changed by the command.
For min and max, integers can be specified, or attribute items can be specified.
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
    

# Device id of SmartThings to add. If not added here, it will not be added as a device
allow_devices:
  - b065a858-1927-fd98-a374-7fc1498e8c76
  - 46955634-09e8-6bc7-0167-a73b2e9182e6
```

# support entity

- number
- switch
- sensor
- binary_sensor
- select

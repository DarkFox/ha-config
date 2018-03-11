"""
Sensors for the ConnectedCars sensors.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.connectedcars/
"""
from datetime import timedelta
import logging

from homeassistant.components.sensor import ENTITY_ID_FORMAT
from custom_components.connectedcars import DOMAIN as CONNECTEDCARS_DOMAIN
from custom_components.connectedcars import ConnectedCarsDevice
from homeassistant.const import (LENGTH_KILOMETERS, VOLUME_LITERS)
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ['connectedcars']

SCAN_INTERVAL = timedelta(minutes=5)


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the ConnectedCars sensor platform."""
    controller = hass.data[CONNECTEDCARS_DOMAIN]['devices']['controller']
    devices = []

    for device in hass.data[CONNECTEDCARS_DOMAIN]['devices']['sensor']:
        devices.append(ConnectedCarsSensor(device, controller))
    add_devices(devices, True)


class ConnectedCarsSensor(ConnectedCarsDevice, Entity):
    """Representation of ConnectedCars sensors."""

    def __init__(self, connectedcars_device, controller, sensor_type=None):
        """Initialize of the sensor."""
        self.current_value = None
        self._unit = None
        self.last_changed_time = None
        self.type = sensor_type
        super().__init__(connectedcars_device, controller)

        if self.type:
            self._name = '{} ({})'.format(self.connectedcars_device.name, self.type)
            self.entity_id = ENTITY_ID_FORMAT.format(
                '{}_{}'.format(self.connectedcars_id, self.type))
        else:
            self.entity_id = ENTITY_ID_FORMAT.format(self.connectedcars_id)

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.current_value

    @property
    def unit_of_measurement(self):
        """Return the unit_of_measurement of the device."""
        return self._unit

    def update(self):
        """Update the state from the sensor."""
        _LOGGER.debug("Updating sensor: %s", self._name)
        self.connectedcars_device.update()
        units = self.connectedcars_device.measurement

        self.current_value = self.connectedcars_device.get_value()
        if self.connectedcars_device.bin_type == 0x5:
            self._unit = VOLUME_LITERS
        elif self.connectedcars_device.bin_type in (0xA, 0xB):
            self._unit = LENGTH_KILOMETERS
        else:
            self._unit = units

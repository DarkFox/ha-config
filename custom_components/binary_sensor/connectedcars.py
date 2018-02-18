"""
Support for ConnectedCars binary sensor.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/binary_sensor.connectedcars/
"""
import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDevice, ENTITY_ID_FORMAT)
from homeassistant.components.connectedcars import DOMAIN as CONNECTEDCARS_DOMAIN, ConnectedCarsDevice

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ['connectedcars']


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the ConnectedCars binary sensor."""
    devices = [
        ConnectedCarsBinarySensor(
            device, hass.data[CONNECTEDCARS_DOMAIN]['controller'], 'connectivity')
        for device in hass.data[CONNECTEDCARS_DOMAIN]['devices']['binary_sensor']]
    add_devices(devices, True)


class ConnectedCarsBinarySensor(ConnectedCarsDevice, BinarySensorDevice):
    """Implement an ConnectedCars binary sensor for parking and charger."""

    def __init__(self, connectedcars_device, controller, sensor_type):
        """Initialise of a ConnectedCars binary sensor."""
        super().__init__(connectedcars_device, controller)
        self._state = False
        self.entity_id = ENTITY_ID_FORMAT.format(self.connectedcars_id)
        self._sensor_type = sensor_type

    @property
    def device_class(self):
        """Return the class of this binary sensor."""
        return self._sensor_type

    @property
    def name(self):
        """Return the name of the binary sensor."""
        return self._name

    @property
    def is_on(self):
        """Return the state of the binary sensor."""
        return self._state

    def update(self):
        """Update the state of the device."""
        _LOGGER.debug("Updating sensor: %s", self._name)
        self.connectedcars_device.update()
        self._state = self.connectedcars_device.get_value()

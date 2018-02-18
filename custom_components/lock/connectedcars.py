"""
Support for ConnectedCars door locks.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/lock.connectedcars/
"""
import logging

from homeassistant.components.lock import ENTITY_ID_FORMAT, LockDevice
from homeassistant.components.connectedcars import DOMAIN as CONNECTEDCARS_DOMAIN
from homeassistant.components.connectedcars import ConnectedCarsDevice
from homeassistant.const import STATE_LOCKED, STATE_UNLOCKED

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ['connectedcars']


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the ConnectedCars lock platform."""
    devices = [ConnectedCarsLock(device, hass.data[CONNECTEDCARS_DOMAIN]['controller'])
               for device in hass.data[CONNECTEDCARS_DOMAIN]['devices']['lock']]
    add_devices(devices, True)


class ConnectedCarsLock(ConnectedCarsDevice, LockDevice):
    """Representation of a ConnectedCars door lock."""

    def __init__(self, connectedcars_device, controller):
        """Initialise of the lock."""
        self._state = None
        super().__init__(connectedcars_device, controller)
        self.entity_id = ENTITY_ID_FORMAT.format(self.connectedcars_id)

    def lock(self, **kwargs):
        pass

    def unlock(self, **kwargs):
        pass

    @property
    def is_locked(self):
        """Get whether the lock is in locked state."""
        return self._state == STATE_LOCKED

    def update(self):
        """Update state of the lock."""
        _LOGGER.debug("Updating state for: %s", self._name)
        self.connectedcars_device.update()
        self._state = STATE_LOCKED if self.connectedcars_device.is_locked() \
            else STATE_UNLOCKED

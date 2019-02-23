"""
Support for the ConnectedCars platform.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/device_tracker.connectedcars/
"""
import logging

from custom_components.connectedcars import DOMAIN as CONNECTEDCARS_DOMAIN
from homeassistant.helpers.event import track_utc_time_change
from homeassistant.util import slugify

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ['connectedcars']


def setup_scanner(hass, config, see, discovery_info=None):
    """Set up the ConnectedCars tracker."""
    ConnectedCarsDeviceTracker(
        hass, config, see,
        hass.data[CONNECTEDCARS_DOMAIN]['devices']['devices_tracker'])
    return True


class ConnectedCarsDeviceTracker(object):
    """A class representing a ConnectedCars device."""

    def __init__(self, hass, config, see, connectedcars_devices):
        """Initialize the ConnectedCars device scanner."""
        self.hass = hass
        self.see = see
        self.devices = connectedcars_devices
        self._update_info()

        track_utc_time_change(
            self.hass, self._update_info, second=range(0, 60, 30))

    def _update_info(self, now=None):
        """Update the device info."""
        for device in self.devices:
            device.update()
            name = device.name
            _LOGGER.debug("Updating device position: %s", name)
            dev_id = slugify(device.uniq_name)
            location = device.get_location()
            lat = location['latitude']
            lon = location['longitude']
            attrs = {
                'trackr_id': dev_id,
                'id': dev_id,
                'name': name
            }
            self.see(
                dev_id=dev_id, host_name=name,
                gps=(lat, lon), attributes=attrs
            )

"""
Support for ConnectedCars
(Also marketd as MinVolkswagen, MinSKODA, and MinSEAT).

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/connectedcars/
"""
from collections import defaultdict
import logging

import voluptuous as vol

from homeassistant.const import (
    ATTR_BATTERY_LEVEL, CONF_PASSWORD, CONF_SCAN_INTERVAL, CONF_USERNAME)
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import discovery
from homeassistant.helpers.entity import Entity
from homeassistant.util import slugify

REQUIREMENTS = ['pyconnectedcars==0.2.1']

DOMAIN = 'connectedcars'

_LOGGER = logging.getLogger(__name__)

CONNECTEDCARS_ID_FORMAT = '{}_{}'
CONNECTEDCARS_ID_LIST_SCHEMA = vol.Schema([int])

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_SCAN_INTERVAL, default=300):
            vol.All(cv.positive_int, vol.Clamp(min=300)),
    }),
}, extra=vol.ALLOW_EXTRA)

NOTIFICATION_ID = 'connectedcars_integration_notification'
NOTIFICATION_TITLE = 'ConnectedCars integration setup'

CONNECTEDCARS_COMPONENTS = [
    'sensor', 'binary_sensor', 'device_tracker'
]


def setup(hass, base_config):
    """Set up of ConnectedCars component."""
    from pyconnectedcars import Controller as connectedcarsAPI
    from pyconnectedcars.Exceptions import ConnectedCarsException

    config = base_config.get(DOMAIN)

    email = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)
    update_interval = config.get(CONF_SCAN_INTERVAL)
    if hass.data.get(DOMAIN) is None:
        try:
            hass.data[DOMAIN] = {
                'controller': connectedcarsAPI(email, password, update_interval),
                'devices': defaultdict(list)
            }
            _LOGGER.debug("Connected to the ConnectedCars API.")
        except ConnectedCarsException as ex:
            if ex.errors[0]['type'] == 'wrong-credentials':
                hass.components.persistent_notification.create(
                    "Error:<br />Please check username and password."
                    "You will need to restart Home Assistant after fixing.",
                    title=NOTIFICATION_TITLE,
                    notification_id=NOTIFICATION_ID)
            else:
                hass.components.persistent_notification.create(
                    "Error:<br />Can't communicate with ConnectedCars API.<br />"
                    "Errors: {}"
                    "You will need to restart Home Assistant after fixing."
                    "".format(ex.errors),
                    title=NOTIFICATION_TITLE,
                    notification_id=NOTIFICATION_ID)
            _LOGGER.error("Unable to communicate with ConnectedCars API: %s",
                          ex.message)
            return False

    all_devices = hass.data[DOMAIN]['controller'].list_vehicles()

    if not all_devices:
        return False

    for device in all_devices:
        hass.data[DOMAIN]['devices'][device.hass_type].append(device)

    for component in CONNECTEDCARS_COMPONENTS:
        discovery.load_platform(hass, component, DOMAIN, {}, base_config)

    return True


class ConnectedCarsDevice(Entity):
    """Representation of a ConnectedCars device."""

    def __init__(self, connectedcars_device, controller):
        """Initialise of the ConnectedCars device."""
        self.connectedcars_device = connectedcars_device
        self.controller = controller
        self._name = self.connectedcars_device.name
        self.connectedcars_id = slugify(self.connectedcars_device.uniq_name)

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def should_poll(self):
        """Return the polling state."""
        return self.connectedcars_device.should_poll

    @property
    def device_state_attributes(self):
        """Return the state attributes of the device."""
        attr = {}

        if self.connectedcars_device.has_battery():
            attr[ATTR_BATTERY_LEVEL] = self.connectedcars_device.battery_level()
        return attr

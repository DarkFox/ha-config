"""
A component which parses DSB's info feed.

Following spec from https://validator.w3.org/feed/docs/rss2.html
"""

import logging
import voluptuous as vol
from datetime import timedelta, datetime
from dateutil import parser, tz
from time import strftime
from operator import attrgetter
from subprocess import check_output
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv
from homeassistant.components.switch import (PLATFORM_SCHEMA)

_LOGGER = logging.getLogger(__name__)

CONF_NAME = 'name'
CONF_DATE_FORMAT = 'date_format'
CONF_SENDER = 'sender'
CONF_MESSAGETYPE = 'messagetype'

DEFAULT_SCAN_INTERVAL = timedelta(hours=1)

COMPONENT_REPO = 'https://github.com/custom-components/sensor.dsb_trafikinfo/'
SCAN_INTERVAL = timedelta(hours=1)
ICON = 'mdi:train'

FEED_URL = 'https://www.dsb.dk/rss-feeds/samlet-trafikinformation/'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NAME): cv.string,
    vol.Optional(CONF_DATE_FORMAT, default='%a, %d %b %Y %H:%M:%S %Z'): cv.string,
    vol.Optional(CONF_SENDER, default=[]): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(CONF_MESSAGETYPE, default=[]): vol.All(cv.ensure_list, [cv.string]),
})

def setup_platform(hass, config, add_devices, discovery_info=None):
    add_devices([DsbTrafikinfoSensor(hass, config)])

class DsbTrafikinfoSensor(Entity):
    def __init__(self, hass, config):
        self.hass = hass
        self._feed = FEED_URL
        self._date_format = config[CONF_DATE_FORMAT]
        self._name = config[CONF_NAME]
        self._senders = config[CONF_SENDER]
        self._messagetypes = config[CONF_MESSAGETYPE]
        self._state = None
        self.hass.data[self._name] = {}
        self.update()

    def update(self):
        import feedparser
        parsedFeed = feedparser.parse(self._feed)

        if not parsedFeed :
            return False
        else:
            self.hass.data[self._name] = {}
            self.hass.data[self._name]['current'] = []
            self.hass.data[self._name]['future'] = []
            now = datetime.now(tz.tzutc())

            for entry in parsedFeed.entries:
                title = entry['title'] if entry['title'] else entry['description']

                if not title:
                    continue

                item = {}
                dates = {}

                for key, value in entry.items():
                    if any(substring in key for substring in ['_detail', 'guidislink', 'headtext']):
                        continue

                    if value == ' ':
                        value = ''
                    if key in ['validfrom', 'validto'] and value:
                        dates[key] = parser.parse(value)
                        item[key+'_parsed'] = dates[key]
                        value = dates[key].strftime(self._date_format)

                    item[key] = value

                if (self._senders and item['sender'] not in self._senders) or (self._messagetypes and item['messagetype'] not in self._messagetypes):
                    continue

                if 'validfrom' in dates and dates['validfrom'] < now and ('validto' not in dates or now < dates['validto']):
                    attribute = 'current'
                elif 'validto' in dates and dates['validto'] < now:
                    # Ignore any expired messages
                    continue
                else:
                    attribute = 'future'

                self.hass.data[self._name][attribute].append(item)

            self.hass.data[self._name]['current'].sort(key=lambda x: x['published_parsed'], reverse=True)
            self.hass.data[self._name]['future'].sort(key=lambda x: x['validfrom_parsed'])

            self._state = len(self.hass.data[self._name]['current'])

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._state

    @property
    def icon(self):
        return ICON

    @property
    def extra_state_attributes(self):
        return self.hass.data[self._name]

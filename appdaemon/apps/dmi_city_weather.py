import appdaemon.plugins.hass.hassapi as hass
import datetime
import requests
from bs4 import BeautifulSoup
#
# DMI City Weather App
#
# Args:
# url: The URL to the DMI City Weather page of your choice. Ex: "http://www.dmi.dk/vejr/til-lands/byvejr/by/vis/DK/1000/K%C3%B8benhavn,%20Danmark/"
# interval: How often the sensor should update (in seconds)

class DMICityWeather(hass.Hass):

    def initialize(self):
        self.log("Init DMI")

        self._entity_id = "sensor.dmi_city_weather"

        self._url = self.args["url"]
        self._interval = self.args["interval"]

        time = datetime.datetime.now()
        self.run_every(self.update_sensor_callback, time, self._interval)
        self.listen_event(self.startup_callback, "plugin_started")

    def startup_callback(self, one, two, kwargs):
        self.log("HA Restarted")
        self.update_sensor_callback("")

    def update_sensor_callback(self, kwargs):
        self.log("Updating DMI")
        raw_html = requests.get(self._url).text
        data = BeautifulSoup(raw_html, 'html.parser')

        headline = data.select_one("#KN h3").get_text()
        dateline = data.select_one("#KN p:nth-of-type(1)").get_text()
        validity = data.select_one("#KN p:nth-of-type(2)").get_text()
        report = data.select_one("#KN p:nth-of-type(3)").get_text()

        attributes = {
            "friendly_name": 'DMI Byvejr',
            "dateline": dateline,
            "validity": validity,
            "report": report,
            "hidden": False
        }

        self.set_state(self._entity_id, state=headline, attributes=attributes)

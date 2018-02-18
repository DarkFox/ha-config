from __future__ import print_function
import appdaemon.plugins.hass.hassapi as hass
import time
import sys
import logging

import pychromecast
import pychromecast.controllers.dashcast as dashcast


class Dashcast(hass.Hass):
    def initialize(self):
        self.log("Init Dashcast")

        self.listen_event(self.cast, "DASHCAST")

    def cast(self, event_name, data, *kwargs):
        receiver = data.get('receiver')
        url = data.get('url')

        self.log("Casting {} to {}".format(url, receiver))

        if not receiver or not url:
            self.log('Both receiver and url must be specified')
            raise Exception

        cast = pychromecast.Chromecast(receiver)

        # casts = pychromecast.get_chromecasts()
        # if not casts:
        #     self.log("No Devices Found")
        #     raise Exception
        #
        # cast_matches = list(filter(lambda x: x.device.friendly_name == receiver, casts))
        # self.log(cast_matches)
        #
        # if not cast_matches:
        #     self.log('No cast device found with that name')
        #     raise Exception
        #
        # cast = cast_matches[0]

        d = dashcast.DashCastController()
        cast.register_handler(d)

        print()
        print(cast.device)
        time.sleep(1)
        print()
        print(cast.status)
        print()
        print(cast.media_controller.status)
        print()

        if not cast.is_idle:
            print("Killing current running app")
            cast.quit_app()
            time.sleep(5)

        time.sleep(1)

        # Test that the callback chain works. This should send a message to
        # load the first url, but immediately after send a message load the
        # second url.

        warning_message = 'If you see this on your TV then something is broken'

        d.load_url('https://home-assistant.io/? ' + warning_message,
                   callback_function=lambda result:
                   d.load_url(url))

import appdaemon.plugins.hass.hassapi as hass
import time
import datetime
import json
import requests

class MySkoda(hass.Hass):

    def initialize(self):
        self._email = self.args["email"]
        self._password = self.args["password"]

        self._interval = self.args["interval"]

        self._entity_prefix = "sensor.myskoda_"
        self._url = "https://skoda.connectedcars.dk/api/graphql"
        self._query = "\n    mutation RootMutationType($email: String, $password: String) {\n      user: login(email: $email, password: $password) {\n        ...userFields\n      }\n    }\n  \n\n\n    fragment userFields on User {\n      \n  id,\n  firstname,\n  lastname,\n  mobile,\n  email,\n  lang,\n  onboardingFinished,\n  token,\n  cars {\n    id,\n    vin,\n    locationName,\n    name,\n    lat,\n    long,\n    fuelLevel,\n    fuelLevelLiter,\n    fuelLevelUpdatedAt,\n    lockedState,\n    lockedStateUpdatedAt,\n    systemsAreOk,\n    oilLevelIsOk,\n    tirePressureIsOk,\n    batteryChargeIsOk,\n    odometer,\n    imageFilename,\n    updatedAt,\n    service {\n      nextServiceInKm,\n      nextServiceInDays\n    },\n    licensePlates {\n      id,\n      licensePlate,\n      createdAt\n    },\n    lamps(listLampStates: true, source: USER) {\n      type,\n      color,\n      frequency,\n      enabled,\n      source,\n      time\n    },\n    incidents(status: ON, dismissed: false, limit: 1000) {\n      id,\n      rule,\n      system {\n        key,\n        headerDanish,\n        headerEnglish,\n        nameDanish,\n        nameEnglish\n      },\n      recommendation {\n        key,\n        descriptionEnglish,\n        descriptionDanish\n      },\n      startTime,\n      context {\n        ... on CarIncidentServiceReminderContext {\n          serviceDate\n        }\n      }\n    }\n  },\n  workshop {\n    id,\n    dealernumber,\n    dealername,\n    phone,\n    bookingurl\n  }\n\n    }\n  "

        self._base_keys = [
            "id",
            "locationName",
            "name",
            "lat",
            "long",
            "fuelLevel",
            "fuelLevelLiter",
            "fuelLevelUpdatedAt",
            "lockedState",
            "lockedStateUpdatedAt",
            "systemsAreOk",
            "oilLevelIsOk",
            "tirePressureIsOk",
            "batteryChargeIsOk",
            "odometer",
            "updatedAt",
            "lamps",
            "incidents"
        ]

        time = datetime.datetime.now()
        self.run_every(self.update_sensor_callback, time, self._interval)
        self.listen_event(self.startup_callback, "plugin_started")

    def startup_callback(self, one, two, kwargs):
        self.log("HA Restarted")
        self.update_sensor_callback("")

    def update_sensor_callback(self, kwargs):
        self.log("Updating MySkoda")

        payload = {
            "query": self._query,
            "variables": {
                "email": self._email,
                "password": self._password
            }
        }

        s = requests.Session()
        s.headers.update({'Content-Type': 'application/json', 'User-Agent': 'okhttp/3.6.0'})

        response = s.post(self._url, data=json.dumps(payload)).json()

        if response.get("errors"):
            self.log(response)
            raise Exception

        data = response['data']
        user = data['user']
        cars = user['cars']

        for car in cars:
            entity_id = "{}{}".format(self._entity_prefix, car['id'])

            attributes = { key: car[key] for key in self._base_keys }
            attributes['nextServiceInKm'] = car.get('service', {}).get('nextServiceInKm')
            attributes['nextServiceInDays'] = car.get('service', {}).get('nextServiceInDays')
            attributes['friendly_name'] = car['name']
            attributes['unit_of_measurement'] = 'KM'
            attributes['icon'] = 'mdi:car'
            self.set_state(entity_id, state=car['odometer'], attributes=attributes)

            # Fuel level
            fuel_entity_id = entity_id + "_fuel_level"
            fuel_attributes = {
                'friendly_name': "{} Fuel Level".format(car['name']),
                'fuel_level_pct': car['fuelLevel'],
                'unit_of_measurement': 'L',
                'icon': 'mdi:fuel',
                'updated_at': car['fuelLevelUpdatedAt']
            }

            self.set_state(fuel_entity_id, state=car['fuelLevelLiter'], attributes=fuel_attributes)

            # Locked
            locked_entity_id = "binary_" + entity_id + "_locked"
            locked_attributes = {
                'friendly_name': "{} Locked".format(car['name']),
                'updated_at': car['lockedStateUpdatedAt'],
                'device_class': "opening",
                'icon': 'mdi:lock-open',
            }
            if car['lockedState'] == 'UNLOCKED':
                locked_state = 'open'
            else:
                locked_state = 'closed'

            self.set_state(locked_entity_id, state=locked_state, attributes=locked_attributes)

            # Problems
            problem_entity_id = "binary_" + entity_id + "_problem"

            problem_attributes = {
                'friendly_name': "{} Problems".format(car['name']),
                'device_class': "problem",
            }

            ok_items = {
                "systemsAreOk": car["systemsAreOk"],
                "oilLevelIsOk": car["oilLevelIsOk"],
                "tirePressureIsOk": car["tirePressureIsOk"],
                "batteryChargeIsOk": car["batteryChargeIsOk"],
            }
            problem_attributes.update(ok_items)
            all_ok = all(v for k,v in ok_items.items())

            issue_items = {
                "lamps": car["lamps"],
                "incidents": car["incidents"]
            }
            problem_attributes.update(issue_items)
            no_issues = all(not v for k,v in issue_items.items())

            if (all_ok and no_issues):
                problem_state = False
            else:
                problem_state = True

            self.set_state(problem_entity_id, state=problem_state, attributes=problem_attributes)

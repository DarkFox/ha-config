room = data.get('room')
logger.info("Activate room light profile: {}".format(room))

hass.services.call('python_script', 'sync_room_light_profile_from_global', { 'room' : room })

party_mode = hass.states.get('input_boolean.party_mode').state
room_state = hass.states.get('input_select.' + room + '_room_state').state
room_light_profile = hass.states.get('input_select.' + room + '_light_profile').state.lower()
room_inactive_light_profile = hass.states.get('input_select.' + room + '_inactive_light_profile').state.lower()

light_script = 'script.light_profile_' + room + '_'

if party_mode == 'on':
    light_script = light_script + 'party'
elif room_state == 'active':
    light_script = light_script + room_light_profile
elif room_state == 'inactive':
    light_script = light_script + room_inactive_light_profile
else:
    light_script = light_script + 'off' 


data = {'entity_id': light_script}

hass.services.call('script', 'turn_on', data)

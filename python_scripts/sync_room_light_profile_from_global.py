room = data.get('room')
logger.info("Sync room light profile: {}".format(room))
room_separate_light_profile = hass.states.get('input_boolean.' + room + '_separate_light_profile').state
room_light_profile_entity_id = 'input_select.' + room + '_light_profile'
light_profile_state = hass.states.get('input_select.light_profile').state

if room_separate_light_profile == 'off':
    data = { 'entity_id' : room_light_profile_entity_id, 'option' : light_profile_state }
    hass.services.call('input_select', 'select_option', data)

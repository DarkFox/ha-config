# Set online input_select option_list from entity state, attribute or string

# Must be entity of the input_select like 'input_select.sonos_favs'
entity_inputselect = data.get('entity_id')[0]

# A entity or string to make a list from
# entity attribute: media_player.buro.source_list
# entity state: media_player.buro
# String with a comma list: 'On,Off'
# String only: 'Pause'
entity_optionsstring = data.get('data_source')

prepend_items = data.get('prepend_items')
append_items = data.get('append_items')

if entity_inputselect is None and entity_optionsstring is None:
    logger.warning('No data!')
    exit()

current_selection = hass.states.get(entity_inputselect).state
option_list = []

if '.' not in entity_optionsstring:
    option_list = entity_optionsstring.split(',')
else:
    entityparts = entity_optionsstring.split('.')
    if len(entityparts) > 2:
        string_elements = hass.states.get(entityparts[0] + '.' + entityparts[1]).attributes[entityparts[2]]
    else:
        string_elements = hass.states.get(entityparts[0] + '.' + entityparts[1]).state

    if ',' in str(string_elements):
        for xe in string_elements:
            if xe:
                option_list.append(xe)
    else:
        option_list.extend(string_elements)

if prepend_items:
    for item in prepend_items:
        option_list.insert(0, item)

if append_items:
    for item in append_items:
        option_list.append(item)

service_data = {'entity_id': entity_inputselect, 'options': option_list}
hass.services.call('input_select', 'set_options', service_data)

if current_selection in option_list:
    service_data = {'entity_id': entity_inputselect, 'option': current_selection}
    hass.services.call('input_select', 'select_option', service_data)


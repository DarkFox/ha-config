import aiohttp
from datetime import datetime
import xmltodict

base_url = "https://dmi.dk/dmidk_byvejrWS/rest/texts/"


async def get_element_with_text(element, needle):
    for key, value in element.items():
        if needle in key:
            return value
    return {}


async def get_first_element_not_in(element, needles):
    for key, value in element.items():
        if key not in needles:
            return value
    return {}


@service
async def get_dmi_weather_report(location_id=None):
    """yaml
    name: Get DMI Weather Report
    description: Get the current DMI weather report
    args:
        location_id:
            description: The location ID to get the weather report for
            required: false
            type: string
    """
    if not location_id:
        raise ValueError("Location ID is required")

    async with aiohttp.ClientSession() as session:
        async with session.get(base_url + str(location_id)) as response:
            response.raise_for_status()
            result = response.json()

            location = result.get('name', '')
            municipality = result.get('municipality', '')

            regiondata = result.get("regiondata", [{}])[0]
            product = regiondata.get('products', [{}])[0]

            timestamp_str = product.get('timestamp', '')
            # What even is this format?? "2024-09-27T20:00:11.377Z[UTC]"
            timestamp = datetime.strptime(
                timestamp_str.replace('[UTC]', '+00:00'),
                '%Y-%m-%dT%H:%M:%S.%fZ%z'
            ) if timestamp_str else None

            xml = xmltodict.parse(product.get("text", ""))
            dmi = xml.get('dmi', {})
            date = dmi.get('dato', {}).get('text', '')

            validity = dmi.get('reggyld', {}).get('text', '')
            title = get_element_with_text(
                dmi, 'overskrift'
            ).get('text', '')

            region_dict = get_element_with_text(
                dmi, 'region'
            )
            region = region_dict.get("@name", "")
            content = get_first_element_not_in(
                region_dict,
                ["@name", "text"]
            ).get("text", "")

            data = {
                'location': location,
                'municipality': municipality,
                'timestamp': timestamp,
                'date': date,
                'validity': validity,
                'title': title,
                'region': region,
                'content': content,
            }

            event.fire('dmi_weather_report', weather_report=data)


@service
async def get_dmi_severe_weather_warnings(location_id=None):
    """yaml
    name: Get DMI Severe Weather Warnings
    description: Get the current DMI severe weather warnings
    args:
        location_id:
            description: The location ID to get the severe weather warnings for
            required: false
            type: string
    """
    if not location_id:
        raise ValueError("Location ID is required")

    async with aiohttp.ClientSession() as session:
        async with session.get(
            base_url + "varsler/geonameid/" + str(location_id)
        ) as response:
            response.raise_for_status()
            result = response.json()

            event.fire('dmi_severe_weather_warnings', severe_weather_warnings=result)

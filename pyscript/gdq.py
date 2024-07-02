import aiohttp
from bs4 import BeautifulSoup

@service
async def gdq_get_bids():
    """yaml
name: Get GDQ Bids
description: Get the current bids from the Games Done Quick tracker. Fires 'gdq_bids' event with the bids.
"""
    url = 'https://tracker.gamesdonequick.com/tracker/bids/SGDQ2024'

    def get_full_url(url):
        return 'https://tracker.gamesdonequick.com' + url

    def get_bid_id(url):
        return int(url.split('/')[-1].strip())

    def parse_amount(amount):
        amount = amount.strip().replace(',', '')
        if not amount or amount == '—':
            return None

        return float(amount[1:])

    def format_currency(amount):
        # Split the number into integer and decimal parts
        integer_part, decimal_part = f'{amount:.2f}'.split('.')
        
        # Reverse the integer part and group by thousands
        integer_part = integer_part[::-1]
        grouped_integer = '.'.join([integer_part[i:i+3] for i in range(0, len(integer_part), 3)])
        
        # Reverse back and combine with the decimal part
        formatted_amount = f'{grouped_integer[::-1]},{decimal_part}'
        
        return formatted_amount

    def parse_text(text) -> str:
        return text.strip()

    def calc_percent(amount, goal):
        if goal == 0:
            return 0.0
        percent = (amount / goal) * 100
        return round(percent, 2)

    def parse_bid_row(row, get_options=True, all_soup=None, bid_total=None):
        columns = row.select('td')
        relative_url = columns[0].find('a')['href']
        bid_id = get_bid_id(relative_url)

        bid = {
            'id': bid_id,
            'name': parse_text(columns[0].find('a').text),
            'link': get_full_url(relative_url),
            'run': parse_text(columns[1].text),
            'description': parse_text(columns[2].text)
        }

        amount = parse_amount(columns[3].text)
        bid['amount'] = amount if amount else 0.0

        goal = None
        if len(columns) > 4:
            goal = parse_amount(columns[4].text)
            if goal:
                bid['goal'] = goal

        if isinstance(amount, float) and isinstance(goal, float):
            bid['percent'] = calc_percent(amount, goal)
        elif isinstance(amount, float) and isinstance(bid_total, float):
            bid['percent'] = calc_percent(amount, bid_total)

        if get_options:
            options = get_bid_options(bid, all_soup=all_soup)
            if options:
                bid['options'] = options

        return bid

    def get_bid_options(bid, all_soup=None):
        options = []
        id_str = f'bidOptionData-{bid["id"]}'
        options_trs = all_soup.select(f'tr#{id_str}')
        if len(options_trs) > 0:
            option_tr = options_trs[0]
            option_rows = option_tr.select('tr.small')
            options = [parse_bid_row(r, get_options=False, bid_total=bid['amount']) for r in option_rows]

        return options

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()
            soup = BeautifulSoup(response.read(), 'html.parser')

            bid_rows = soup.select('div.container-fluid > table > tr.small')

            if not bid_rows:
                raise ValueError('No bid rows found')

            bids = [parse_bid_row(r, all_soup=soup) for r in bid_rows]

            event.fire('gdq_bids', bids=bids)

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

    def parse_text(text) -> str:
        return text.strip()


    def parse_bid_row(row, get_options=True, all_soup=None):
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
        bid['amount'] = int(amount) if amount else None

        goal = parse_amount(columns[4].text) if len(columns) > 4 else None
        bid['goal'] = int(goal) if goal else None

        if goal and isinstance(amount, float) and isinstance(goal, float):
            percent = (amount / bid['goal']) * 100
            bid['percent'] = round(percent, 2)

        if get_options:
            options = get_bid_options(bid_id, all_soup=all_soup)
            if options:
                bid['options'] = options

        return bid

    def get_bid_options(bid_id, all_soup=None):
        options = []
        id_str = f'bidOptionData-{bid_id}'
        options_trs = all_soup.select(f'tr#{id_str}')
        if len(options_trs) > 0:
            option_tr = options_trs[0]
            option_rows = option_tr.select('tr.small')
            options = [parse_bid_row(r, get_options=False) for r in option_rows]

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

import aiohttp
from datetime import datetime
from datetime import timezone
from bs4 import BeautifulSoup
from bs4 import XMLParsedAsHTMLWarning
import warnings

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

base_url = "https://tracker.gamesdonequick.com"


async def get_runs(uri):
    async with aiohttp.ClientSession() as session:
        async with session.get(base_url + uri) as runs_response:
            runs_response.raise_for_status()
            runs_soup = BeautifulSoup(runs_response.read(), "html.parser")

            run_headers = runs_soup.select(
                "table.table-striped > thead > tr > th"
            )
            columns = [header.text.strip() for header in run_headers]

            run_rows = runs_soup.select("table.table-striped > tr")
            runs = []
            for run_row in run_rows:
                values = [cell.text.strip() for cell in run_row.select("td")]
                run = dict(zip(columns, values))
                runs.append(run)

            return runs


async def gdq_event_runs_uri(uri):
    async with aiohttp.ClientSession() as session:
        async with session.get(base_url + uri) as evt_response:
            evt_response.raise_for_status()
            evt_soup = BeautifulSoup(evt_response.read(), "html.parser")
            buttons = evt_soup.select("p.center-block a.btn-block")
            for button in buttons:
                if "View Runs" in button.text:
                    run_count = int(button.text.split("(")[1].split(")")[0])
                    if run_count > 0:
                        return button["href"]
    return False


async def get_gdq_event_info():
    next_event = None

    async with aiohttp.ClientSession() as session:
        async with session.get(base_url + "/tracker/events/") as response:
            response.raise_for_status()
            soup = BeautifulSoup(response.read(), "html.parser")

            gdq_events = soup.select("a.list-group-item")

            if not gdq_events:
                return None

            # Find the first event with runs
            for gdq_event in gdq_events:
                if "All Events" in gdq_event.text:
                    continue

                href = gdq_event["href"]
                runs_uri = gdq_event_runs_uri(href)
                if runs_uri:
                    runs = get_runs(runs_uri)

                    if runs:
                        # fmt: 2025-02-06T13:40:00-05:00
                        start_time = runs[0]["Start Time"]
                        end_time = runs[-1]["Start Time"]

                        parsed_end_time = datetime.strptime(
                            end_time, "%Y-%m-%dT%H:%M:%S%z"
                        )

                        if datetime.now(timezone.utc) > parsed_end_time:
                            break

                        next_event = {
                            "name": gdq_event.text,
                            "url": base_url + href,
                            "id": href.split("/")[-1],
                            "runs_uri": runs_uri,
                            "start_time": start_time,
                            "end_time": end_time,
                        }

    return next_event


@service  # noqa: F821
async def get_gdq_event():
    """yaml
    name: Get GDQ Event
    description: Get the current GDQ event data
    """
    data = {
        "name": None,
        "url": None,
        "id": None,
        "runs_uri": None,
        "start_date": None,
        "end_date": None
    }

    gdq_event = get_gdq_event_info()

    if gdq_event:
        data = gdq_event

    event.fire("gdq_event", event=data)  # noqa: F821
    return data


@service  # noqa: F821  # noqa: F821
async def gdq_get_donation_stats():
    """yaml
    name: Get GDQ Donation Stats
    description: Get the current donation stats from the GDQ tracker.
    """
    if not sensor.gdq_event:  # noqa: F821
        return None

    url = f"{base_url}/tracker/event/{sensor.gdq_event.id}"  # noqa: F821

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()
            soup = BeautifulSoup(response.read(), "html.parser")
            donation_stats_string = soup.select_one(
                "h2.text-center small"
            ).text

            donation_stats = {
                "total": None,
                "count": None,
                "max": None,
                "average": None,
                "median": None,
            }

            for line in donation_stats_string.split("\n"):
                if "(" in line:
                    total, count = line.split("(")
                    donation_stats["total"] = float(
                        total.replace("$", "").replace(",", "")
                    )
                    donation_stats["count"] = int(count.split(")")[0])
                elif "/" in line and "Max" not in line:
                    max_, avg, median = line.split("/")
                    donation_stats["max"] = float(
                        max_.replace("$", "").replace(",", "")
                    )
                    donation_stats["average"] = float(
                        avg.replace("$", "").replace(",", "")
                    )
                    donation_stats["median"] = float(
                        median.replace("$", "").replace(",", "")
                    )

            event.fire(  # noqa: F821
                "gdq_donation_stats", stats=donation_stats
            )  # Longer comment to avoid formatter collapsing this line
            return total


@service  # noqa: F821
async def gdq_get_bids():
    """yaml
    name: Get GDQ Bids
    description: Get the current bids from the GDQ tracker.
    """
    if not sensor.gdq_event:  # noqa: F821
        event.fire("gdq_bids", bids=[])  # noqa: F821
        return None

    url = f"{base_url}/tracker/bids/{sensor.gdq_event.id}"  # noqa: F821

    def get_full_url(uri):
        return base_url + uri

    def get_bid_id(uri):
        return int(uri.split("/")[-1].strip())

    def parse_amount(amount):
        amount = amount.strip().replace(",", "")
        if not amount or amount == "—":
            return None

        return float(amount[1:])

    def format_currency(amount):
        # Split the number into integer and decimal parts
        integer_part, decimal_part = f"{amount:.2f}".split(".")

        # Reverse the integer part and group by thousands
        integer_part = integer_part[::-1]
        grouped_integer = ".".join(
            [integer_part[i: i + 3] for i in range(0, len(integer_part), 3)]
        )

        # Reverse back and combine with the decimal part
        formatted_amount = f"{grouped_integer[::-1]},{decimal_part}"

        return formatted_amount

    def parse_text(text) -> str:
        return text.strip()

    def calc_percent(amount, goal):
        if goal == 0:
            return 0.0
        percent = (amount / goal) * 100
        return round(percent, 2)

    def parse_bid_row(row, get_options=True, all_soup=None, bid_total=None):
        columns = row.select("td")
        uri = columns[0].find("a")["href"]
        bid_id = get_bid_id(uri)

        bid = {
            "id": bid_id,
            "name": parse_text(columns[0].find("a").text),
            "link": get_full_url(uri),
            "run": parse_text(columns[1].text),
            "description": parse_text(columns[2].text),
        }

        amount = parse_amount(columns[3].text)
        bid["amount"] = amount if amount else 0.0

        goal = None
        if len(columns) > 4:
            goal = parse_amount(columns[4].text)
            if goal:
                bid["goal"] = goal

        if isinstance(amount, float) and isinstance(goal, float):
            bid["percent"] = calc_percent(amount, goal)
        elif isinstance(amount, float) and isinstance(bid_total, float):
            bid["percent"] = calc_percent(amount, bid_total)

        if get_options:
            options = get_bid_options(bid, all_soup=all_soup)
            if options:
                bid["options"] = options

        return bid

    def get_bid_options(bid, all_soup=None):
        options = []
        id_str = f'bidOptionData-{bid["id"]}'
        options_trs = all_soup.select(f"tr#{id_str}")
        if len(options_trs) > 0:
            option_tr = options_trs[0]
            option_rows = option_tr.select("tr.small")
            options = [
                parse_bid_row(r, get_options=False, bid_total=bid["amount"])
                for r in option_rows
            ]

        return options

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()
            soup = BeautifulSoup(response.read(), "html.parser")

            bid_rows = soup.select("div.container-fluid table tr.small")

            if not bid_rows:
                event.fire("gdq_bids", bids=[])  # noqa: F821
                return None

            bids = [parse_bid_row(r, all_soup=soup) for r in bid_rows]

            event.fire("gdq_bids", bids=bids)  # noqa: F821

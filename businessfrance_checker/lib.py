"""businessfrance_checker lib"""

from os import getenv
from os.path import exists
from hashlib import sha256
import warnings
from json import dumps, loads
import requests
from requests.adapters import HTTPAdapter, Retry
from dotenv import load_dotenv


def try_request(func, *args, **kwargs):
    """try request"""
    res = None
    s = requests.Session()
    retries = Retry(
        total=20,
        backoff_factor=1.5,
        status_forcelist=[500, 502, 503, 504],
    )
    s.mount("https://", HTTPAdapter(max_retries=retries))

    try:
        if func == "get":
            res = s.get(*args, **kwargs, timeout=1)
        else:
            res = s.post(*args, **kwargs, timeout=1)
    except Exception as _e:
        print("Error during request")
        # print(_e)
        exit(1)
    return res


def make_sha(item):
    """return a sha256 hash"""
    obj = {"id": item["id"], "title": item["missionTitle"]}
    j = dumps(obj, indent=4)
    m = sha256()
    m.update(j.encode())
    return m.hexdigest()


def load_data(path_to_filename):
    """load the data"""
    if not exists(path_to_filename):
        with open(path_to_filename, "w", encoding="utf-8") as file:
            file.write("[]")
    try:
        with open(path_to_filename, "r", encoding="utf-8") as file:
            loaded = loads(file.read())
    except Exception as _e:
        loaded = []
    return loaded


def notify(url, text):
    """webhook notify"""
    try_request(
        "post",
        url,
        json={
            "username": "businessfrance checker",
            "content": text,
            "avatar_url": "https://business-france-v2.cdn.prismic.io/business-france-v2/Zvq0FrVsGrYSwJYa_Logo_BF.svg",
        },
    )


def format_offer(offer):
    """format the offer for the webhook"""
    text = f"{offer['missionTitle']}\n{offer['organizationName']}\n"
    text += f"{offer['countryName']}\n{offer['cityName']} - {offer['creationDate']}\n"
    text += f"https://mon-vie-via.businessfrance.fr/en/offres/{offer['id']}"
    return text


def main():
    """main function"""
    warnings.filterwarnings("ignore")
    load_dotenv()
    data_filename = getenv("DATA_FILENAME")
    if data_filename is None:
        data_filename = "data.json"
    webhook_url = getenv("WEBHOOK_URL")
    if webhook_url is None:
        print("No webhook url in env WEBHOOK_URL")
        exit(1)

    response = try_request(
        "post",
        "https://civiweb-api-prd.azurewebsites.net/api/Offers/search",
        json={
            "limit": 100,
            "skip": 0,
            "sort": [
                "0",
            ],
            "activitySectorId": [],
            "missionsTypesIds": [],
            "missionsDurations": [],
            "gerographicZones": [],
            "countriesIds": [],
            "studiesLevelId": [],
            "companiesSizes": [],
            "specializationsIds": [],
            "entreprisesIds": [
                0,
            ],
            "missionStartDate": None,
            "query": None,
        },
    )

    try:
        resp = response.json()
    except Exception as e:
        print("Error during parsing")
        print(e)
        print(response.text)
        resp = {}

    if "result" not in resp:
        print("No result")
        print(resp)
        exit(1)

    resp = resp["result"]

    current_data = load_data(data_filename)
    current_data_set = set(current_data)
    to_add = []
    found = []

    for one_item in resp:
        result_sha = str(make_sha(one_item))
        if result_sha not in current_data_set:
            found.append(one_item)
            to_add.append(result_sha)

    print(f"Found {len(found)} new items")
    for one_item in found:
        smol_item = format_offer(one_item)
        smol_item += "\n-------------------"
        notify(webhook_url, smol_item)
        print("New item found")

    final = current_data + to_add

    with open(data_filename, "w", encoding="utf-8") as file:
        txt = dumps(final, indent=4)
        file.write(txt)

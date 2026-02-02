import requests
import time

class TradeAPI:
    SEARCH_URL_BASE = "https://www.pathofexile.com/api/trade2/search/poe2/"
    FETCH_URL_BASE = "https://www.pathofexile.com/api/trade2/fetch/"
    DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:146.0) Gecko/20100101 Firefox/146.0"

    def __init__(self, session_id=None):
        self.session_id = session_id
        self.headers = {
            "User-Agent": self.DEFAULT_USER_AGENT,
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        if self.session_id:
            self.headers["Cookie"] = f"POESESSID={self.session_id}"

    def search(self, query, league="Fate of the Vaal"):
        url = f"{self.SEARCH_URL_BASE}{league}"
        payload = {
            "query": query,
            "sort": {"price": "asc"}
        }
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()

    def fetch(self, ids, query_id=None):
        if not ids:
            return {"result": []}
            
        id_string = ",".join(ids)
        url = f"{self.FETCH_URL_BASE}{id_string}"
        params = {"realm": "poe2"}
        if query_id:
            params["query"] = query_id
            
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

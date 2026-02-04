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

    def _request(self, method, url, **kwargs):
        max_retries = 4  # 4 total attempts (3 retries + 1 initial)
        retry_delay_429 = 2  # Base delay for 429 (rate limit)
        retry_delay_502 = 5  # Base delay for 502 (server error)
        last_response = None

        for attempt in range(max_retries):
            response = requests.request(method, url, headers=self.headers, **kwargs)
            last_response = response
            
            if response.status_code == 429:
                wait_time = retry_delay_429 * (2 ** attempt)
                retry_after = response.headers.get("Retry-After")
                if retry_after:
                    try:
                        wait_time = int(retry_after) + 1
                    except ValueError:
                        pass
                
                print(f"Rate limited (429). Waiting {wait_time}s before retry {attempt + 1}/{max_retries}...")
                time.sleep(wait_time)
                continue
            
            if response.status_code == 502:
                wait_time = retry_delay_502 * (2 ** attempt)
                print(f"502 Bad Gateway from GGG server. Waiting {wait_time}s before retry {attempt + 1}/{max_retries}...")
                time.sleep(wait_time)
                continue
            
            response.raise_for_status()
            return response.json()
        
        if last_response is not None:
            last_response.raise_for_status()
        raise Exception("Request failed after maximum retries")

    def search(self, query, league="Fate of the Vaal"):
        import urllib.parse
        encoded_league = urllib.parse.quote(league)
        url = f"{self.SEARCH_URL_BASE}{encoded_league}"
        
        # Ensure sort is not inside query (common mistake in client code)
        sort = query.pop("sort", {"price": "asc"})
        
        payload = {
            "query": query,
            "sort": sort
        }
        response = self._request("POST", url, json=payload)
        
        if isinstance(response, list):
            return {"result": response, "total": len(response)}
        return response or {}

    def fetch(self, ids, query_id=None):
        if not ids:
            return {"result": []}
            
        id_string = ",".join(ids)
        url = f"{self.FETCH_URL_BASE}{id_string}"
        params = {"realm": "poe2"}
        if query_id:
            params["query"] = query_id
            
        response = self._request("GET", url, params=params)
        
        if isinstance(response, list):
            return {"result": response}
        return response or {"result": []}

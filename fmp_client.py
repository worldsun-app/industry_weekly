import requests
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class FMPClient:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("FMP API key is required.")
        self.api_key = api_key
        self.base_url = "https://financialmodelingprep.com"

    def _request(self, endpoint: str, params: dict = None) -> Optional[dict]:
        if params is None:
            params = {}
        params['apikey'] = self.api_key

        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            if not data:
                logger.warning(f"No data found for endpoint {url} with params {params}")
                return None
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching from {url}: {e}")
            return None
    
    def get_sp500(self):
        endpoint = "api/v3/sp500_constituent"
        sp500_data = self._request(endpoint)
        return sp500_data

    def get_market_caps_for_list(self, symbols: list[str]):
        """Gets market capitalization for a list of symbols in a single API call."""
        if not symbols:
            return None
        symbols_string = ",".join(symbols)
        endpoint = f"api/v3/market-capitalization/{symbols_string}"
        market_cap_data = self._request(endpoint)
        return market_cap_data

    def get_available_sectors(self):
        endpoint = f"stable/available-sectors"
        available_sectors = self._request(endpoint)
        return available_sectors
    
    def get_sector_pe_snapshot(self, date: str = None):
        endpoint = f"stable/sector-pe-snapshot"
        sector_pe_snapshot = self._request(endpoint, params={"date": date})
        return sector_pe_snapshot
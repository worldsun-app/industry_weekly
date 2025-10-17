import requests
import logging
from typing import Optional
import datetime

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
    
    def get_symbol_price(self, symbols: list[str]):
        """Gets symbol price for a list of symbols in a single API call."""
        if not symbols:
            return None
        symbols_string = ",".join(symbols)
        endpoint = "stable/batch-quote" # Corrected endpoint
        symbol_data = self._request(endpoint, params={"symbols": symbols_string})  
        if symbol_data:
            extracted_prices = []
            for stock_info in symbol_data:
                extracted_prices.append({
                    "symbol": stock_info.get("symbol"),
                    "price": stock_info.get("price"),
                    "changePercentage": stock_info.get("changePercentage")
                })
            return extracted_prices
    
    def get_ETF_ROI(self, symbol: str):
        endpoint = f"/stable/stock-price-change"
        params = {"symbol": symbol}
        etf_data_list = self._request(endpoint, params=params)
        
        if etf_data_list and isinstance(etf_data_list, list) and len(etf_data_list) > 0:
            etf_data = etf_data_list[0] # Get the first dictionary from the list
            etf_roi_data = {
                "1D": etf_data.get("1D"),
                "5D": etf_data.get("5D"),
                "1M": etf_data.get("1M"),
                "3M": etf_data.get("3M"),
                "6M": etf_data.get("6M"),
                "1Y": etf_data.get("1Y")
            }
            return etf_roi_data
        return None

    def get_historical_sector_pe(self, sector: str):
        """Gets the historical PE for a given sector for the past year."""
        if not sector:
            return None
        
        to_date = datetime.date.today()
        from_date = to_date - datetime.timedelta(days=365)

        endpoint = "stable/historical-sector-pe"
        params = {
            "sector": sector,
            "from": from_date.strftime('%Y-%m-%d'),
            "to": to_date.strftime('%Y-%m-%d')
        }
        
        historical_data = self._request(endpoint, params=params)
        return historical_data

    def get_available_sectors(self):
        endpoint = f"stable/available-sectors"
        available_sectors = self._request(endpoint)
        return available_sectors
    
    def get_sector_pe_snapshot(self, date: str = None, sector: str = None):
        if date is None:
            today = datetime.date.today().strftime('%Y-%m-%d')
            date = today

        endpoint = f"stable/sector-pe-snapshot"
        params = {"date": date}
        if sector:
            params["sector"] = sector

        sector_pe_snapshot = self._request(endpoint, params=params)
        return sector_pe_snapshot
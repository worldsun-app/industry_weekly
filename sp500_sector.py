import os
import logging
import time
from collections import defaultdict
from datetime import date, timedelta

from dotenv import load_dotenv
from google.cloud import firestore

from fmp_client import FMPClient
from firestore_service import get_latest_report

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SP500DataUpdater:
    def __init__(self):
        load_dotenv()
        logger.info("正在初始化客戶端...")
        
        fmp_api_key = os.getenv('FMP_API_KEY')
        if not fmp_api_key:
            raise ValueError("錯誤：找不到 FMP_API_KEY 環境變數。")
            
        self.fmp_client = FMPClient(api_key=fmp_api_key)
        
        try:
            self.db = firestore.Client()
            logger.info("FMP 和 Firestore 客戶端初始化成功。")
        except Exception as e:
            logger.error(f"初始化 Firestore client 時發生錯誤: {e}")
            self.db = None

    def update_top10_by_market_cap_per_sector(self):
        if not self.db:
            logger.error("Firestore client 未初始化，無法執行。")
            return

        logger.info("--- 開始更新市值前十名資料 ---")
        sp500_stocks = self.fmp_client.get_sp500()
        if not sp500_stocks:
            logger.error("無法獲取 S&P 500 列表，任務終止。")
            return

        stocks_by_sector = defaultdict(list)
        for stock in sp500_stocks:
            if stock.get('sector'):
                stocks_by_sector[stock['sector']].append(stock)

        top10_by_sector = {}
        for sector, stocks in stocks_by_sector.items():
            symbols_in_sector = [stock['symbol'] for stock in stocks]
            market_cap_data = self.fmp_client.get_market_caps_for_list(symbols_in_sector)
            if not market_cap_data:
                logger.warning(f"無法獲取 '{sector}' 產業的市值資料，已略過。")
                continue
            sorted_stocks = sorted(market_cap_data, key=lambda x: x.get('marketCap', 0), reverse=True)
            top10_stocks = sorted_stocks[:10]
            top10_symbols = [stock['symbol'] for stock in top10_stocks]
            if top10_symbols:
                price_data = self.fmp_client.get_symbol_price(top10_symbols)
                price_map = {item['symbol']: {'price': item.get('price'), 'changePercentage': item.get('changePercentage')} for item in price_data}
                for stock in top10_stocks:
                    stock_price_info = price_map.get(stock['symbol'])
                    if stock_price_info:
                        stock['price'] = stock_price_info['price']
                        stock['changePercentage'] = stock_price_info['changePercentage']

            top10_by_sector[sector] = top10_stocks
        try:
            collection_name = "industry_data"
            batch = self.db.batch()
            for sector, top_stocks in top10_by_sector.items():
                doc_ref = self.db.collection(collection_name).document(sector)
                batch.set(doc_ref, {"top_stocks": top_stocks}, merge=True)
            batch.commit()
            logger.info(f"市值前十名資料已成功合併寫入 '{collection_name}' 集合！")
        except Exception as e:
            logger.error(f"寫入市值資料到 Firestore 時發生錯誤: {e}")

    def update_sector_details(self):
        """
        遍歷所有已知的產業，更新其報告摘要、對應的 ETF 報酬率資料以及當日的 PE 值。
        """
        if not self.db:
            logger.error("Firestore client 未初始化，無法執行。")
            return
        SECTOR_ETF_MAP = {
            "Communication Services": "XLC",
            "Consumer Cyclical": "XLY",
            "Consumer Defensive": "XLP",
            "Energy": "XLE",
            "Financial Services": "XLF",
            "Healthcare": "XLV",
            "Industrials": "XLI",
            "Basic Materials": "XLB",
            "Real Estate": "XLRE",
            "Technology": "XLK",
            "Utilities": "XLU"
        }

        logger.info("--- 開始更新產業詳細資料 (ETF ROI, PE, 摘要) ---")
        
        pe_snapshot = self.fmp_client.get_sector_pe_snapshot()
        if not pe_snapshot:
            logger.warning("無法從 FMP 獲取 PE 快照資料，PE 資料將不會被更新。")
            pe_map = {}
        else:
            pe_map = {item.get('sector'): item.get('pe') for item in pe_snapshot}

        try:
            docs = self.db.collection("industry_data").stream()
            sectors = [doc.id for doc in docs]
            
            batch = self.db.batch()
            for sector in sectors:
                latest_report = get_latest_report(sector)
                preview_summary = latest_report.get('preview_summary', '') if latest_report else ''
                etf_roi_data = {}
                cleaned_sector = sector.strip()
                etf_symbol = SECTOR_ETF_MAP.get(cleaned_sector)
                if etf_symbol:
                    try:
                        roi_data = self.fmp_client.get_ETF_ROI(etf_symbol)
                        if roi_data:
                            etf_roi_data.update(roi_data)
                    except Exception as e:
                        logger.error(f"為 symbol '{etf_symbol}' 獲取 ETF ROI 時發生錯誤: {e}")
                pe_value = pe_map.get(sector)
                if pe_value is not None:
                    etf_roi_data['pe_today'] = round(pe_value, 2)
                doc_data = {
                    'preview_summary': preview_summary,
                    'etf_roi': etf_roi_data if etf_roi_data else None
                }
                try:
                    pe_history = self.fmp_client.get_historical_sector_pe(sector)
                    if pe_history and isinstance(pe_history, list) and len(pe_history) > 0:
                        pe_values = [item['pe'] for item in pe_history]
                        pe_high_1y = max(pe_values)
                        pe_low_1y = min(pe_values)

                        doc_data['pe_high_1y'] = round(pe_high_1y, 2)
                        doc_data['pe_low_1y'] = round(pe_low_1y, 2)
                except Exception as e:
                    logger.error(f"為 sector '{sector}' 處理歷史 PE 時發生錯誤: {e}")
                
                doc_ref = self.db.collection("industry_data").document(sector)
                batch.set(doc_ref, doc_data, merge=True)

            batch.commit()
            logger.info("產業詳細資料已成功合併寫入 'industry_data' 集合！")
        except Exception as e:
            logger.error(f"更新產業詳細資料到 Firestore 時發生錯誤: {e}")

    def update_sp500_etf_roi(self):
        if not self.db:
            logger.error("Firestore client 未初始化，無法執行。")
            return
        try:
            spy_roi_data = self.fmp_client.get_ETF_ROI("SPY")
            if spy_roi_data:
                doc_ref = self.db.collection("industry_data").document("S&P 500")
                doc_ref.set({"etf_roi": spy_roi_data}, merge=True)
                logger.info("S&P 500 (SPY) ETF ROI 資料已成功合併寫入！")
            else:
                logger.warning("無法獲取 SPY 的 ETF ROI 資料。")
        except Exception as e:
            logger.error(f"更新 S&P 500 (SPY) ETF ROI 時發生錯誤: {e}")

    def update_market_breadth(self):
        """計算每個產業的市場廣度指標（股價高於200日均線的公司佔比）。"""
        if not self.db:
            logger.error("Firestore client 未初始化，無法執行。")
            return

        logger.info("--- 開始更新市場廣度指標 (200日均線) ---")

        # 1. 獲取 S&P 500 公司列表並按產業分組
        sp500_stocks = self.fmp_client.get_sp500()
        if not sp500_stocks:
            logger.error("無法獲取 S&P 500 列表，任務終止。")
            return

        stocks_by_sector = defaultdict(list)
        for stock in sp500_stocks:
            if stock.get('sector') and stock.get('symbol'):
                stocks_by_sector[stock['sector']].append(stock['symbol'])

        # 2. 遍歷每個產業，計算廣度指標
        batch = self.db.batch()
        for sector, symbols in stocks_by_sector.items():
            if not symbols:
                continue

            above_sma_count = 0
            total_count = len(symbols)
            logger.info(f"正在處理產業: {sector} ({total_count} 家公司)")

            for symbol in symbols:
                try:
                    indicator_data = self.fmp_client.get_sma(symbol)
                    logger.info(f"  - {symbol}: Indicator data: {indicator_data}") # Log indicator data

                    if indicator_data:
                        current_price = indicator_data.get('close')
                        sma_200 = indicator_data.get('sma')
                        logger.info(f"    - Price: {current_price}, SMA(200): {sma_200}") # Log price and SMA

                        if current_price is not None and sma_200 is not None:
                            if current_price > sma_200:
                                above_sma_count += 1
                    time.sleep(0.1)

                except Exception as e:
                    logger.error(f"處理 {symbol} 時發生錯誤: {e}")

            if total_count > 0:
                breadth_percentage = (above_sma_count / total_count) * 100
                logger.info(f"產業 '{sector}' 的市場廣度指標: {above_sma_count}/{total_count} = {breadth_percentage:.2f}%") # Log final calculation

                doc_ref = self.db.collection("industry_data").document(sector)
                batch.set(doc_ref, {"market_breadth_200d": round(breadth_percentage, 1)}, merge=True)

        try:
            batch.commit()
            logger.info("市場廣度指標已成功合併寫入 'industry_data' 集合！")
        except Exception as e:
            logger.error(f"寫入市場廣度指標到 Firestore 時發生錯誤: {e}")

    def update_all_industry_data(self):
        """
        執行所有產業資料的更新任務。
        """
        logger.info("=== 開始全面更新產業資料 ===")
        self.update_top10_by_market_cap_per_sector()
        self.update_sector_details()
        self.update_sp500_etf_roi()
        self.update_market_breadth()
        logger.info("=== 所有產業資料更新完畢 ===")

def run_sp500_update():
    updater = SP500DataUpdater()
    updater.update_all_industry_data()

if __name__ == '__main__':
    run_sp500_update()
import os
import logging
import time
from collections import defaultdict
from datetime import date, timedelta

from dotenv import load_dotenv
from google.cloud import firestore

from fmp_client import FMPClient

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SP500DataUpdater:
    def __init__(self):
        """初始化 FMP 和 Firestore 客戶端。"""
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

    def update_top5_by_market_cap_per_sector(self):
        if not self.db:
            logger.error("Firestore client 未初始化，無法執行。")
            return

        logger.info("--- 開始更新市值前五名資料 ---")
        sp500_stocks = self.fmp_client.get_sp500()
        if not sp500_stocks:
            logger.error("無法獲取 S&P 500 列表，任務終止。")
            return

        stocks_by_sector = defaultdict(list)
        for stock in sp500_stocks:
            if stock.get('sector'):
                stocks_by_sector[stock['sector']].append(stock)

        top5_by_sector = {}
        for sector, stocks in stocks_by_sector.items():
            symbols_in_sector = [stock['symbol'] for stock in stocks]
            market_cap_data = self.fmp_client.get_market_caps_for_list(symbols_in_sector)
            if not market_cap_data:
                logger.warning(f"無法獲取 '{sector}' 產業的市值資料，已略過。")
                continue
            sorted_stocks = sorted(market_cap_data, key=lambda x: x.get('marketCap', 0), reverse=True)
            top5_by_sector[sector] = sorted_stocks[:5]

        try:
            collection_name = "industry_data"
            batch = self.db.batch()
            for sector, top_stocks in top5_by_sector.items():
                doc_ref = self.db.collection(collection_name).document(sector)
                batch.set(doc_ref, {"top_stocks": top_stocks}, merge=True)
            batch.commit()
            logger.info(f"市值前五名資料已成功合併寫入 '{collection_name}' 集合！")
        except Exception as e:
            logger.error(f"寫入市值資料到 Firestore 時發生錯誤: {e}")

    def update_weekly_pe_ratios(self):
        if not self.db:
            logger.error("Firestore client 未初始化，無法執行。")
            return

        logger.info("--- 開始更新 PE 週變動資料 ---")
        today = date.today()
        pe_by_sector = defaultdict(list)

        for i in range(7):
            target_date = today - timedelta(days=i)
            date_str = target_date.strftime('%Y-%m-%d')
            daily_pe_snapshot = self.fmp_client.get_sector_pe_snapshot(date_str)
            if daily_pe_snapshot:
                for item in daily_pe_snapshot:
                    if item.get('sector') and item.get('pe') is not None:
                        pe_by_sector[item['sector']].append({'date': date_str, 'pe': item['pe']})
            time.sleep(0.2)

        try:
            collection_name = "industry_data"
            batch = self.db.batch()
            for sector, history in pe_by_sector.items():
                if len(history) < 2:
                    continue
                history.sort(key=lambda x: x['date'], reverse=True)
                pe_today = history[0]['pe']
                pe_7_days_ago = history[-1]['pe']
                pe_weekly_change_percent = ((pe_today - pe_7_days_ago) / pe_7_days_ago) * 100 if pe_7_days_ago != 0 else float('inf')

                doc_data = {
                    'sector': sector,
                    'pe_today': pe_today,
                    'pe_7_days_ago': pe_7_days_ago,
                    'pe_weekly_change_percent': round(pe_weekly_change_percent, 2),
                    'pe_history': history
                }
                doc_ref = self.db.collection(collection_name).document(sector)
                batch.set(doc_ref, doc_data, merge=True)
            batch.commit()
            logger.info(f"PE 週變動資料已成功合併寫入 '{collection_name}' 集合！")
        except Exception as e:
            logger.error(f"寫入 PE 資料到 Firestore 時發生錯誤: {e}")

    def update_all_industry_data(self):
        """
        執行所有產業資料的更新任務。
        """
        logger.info("=== 開始全面更新產業資料 ===")
        self.update_top5_by_market_cap_per_sector()
        self.update_weekly_pe_ratios()
        logger.info("=== 所有產業資料更新完畢 ===")

if __name__ == '__main__':
    updater = SP500DataUpdater()
    updater.update_all_industry_data()
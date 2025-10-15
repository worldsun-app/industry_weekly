
import os
import logging
from dotenv import load_dotenv
from google.cloud import firestore

from fmp_client import FMPClient

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_sp500_sectors_in_firestore():
    load_dotenv()
    
    fmp_api_key = os.getenv('FMP_API_KEY')
    if not fmp_api_key:
        logger.error("錯誤：找不到 FMP_API_KEY 環境變數。")
        return

    fmp_client = FMPClient(api_key=fmp_api_key)
    
    try:
        db = firestore.Client()
        logger.info("Firestore client 初始化成功。")
    except Exception as e:
        logger.error(f"初始化 Firestore client 時發生錯誤: {e}")
        return

    # --- 2. 從 FMP 獲取資料 ---
    logger.info("正在從 FMP API 獲取 S&P 500 成分股列表...")
    sp500_stocks = fmp_client.get_sp500()

    if not sp500_stocks:
        logger.error("無法從 FMP 獲取 S&P 500 資料，程式終止。")
        return

    logger.info(f"成功獲取 {len(sp500_stocks)} 筆成分股資料。")

    # --- 3. 將資料寫入 Firestore ---
    try:
        collection_name = "sp500_symbols"
        batch = db.batch()
        
        logger.info(f"準備將資料批次寫入 Firestore 的 '{collection_name}' 集合...")

        for stock in sp500_stocks:
            symbol = stock.get('symbol')
            if not symbol:
                logger.warning(f"找到一筆沒有 symbol 的資料，已略過: {stock}")
                continue
            
            # 使用股票代碼作為文件 ID
            doc_ref = db.collection(collection_name).document(symbol)
            # 將整筆股票資料存入文件
            batch.set(doc_ref, stock)

        # 提交批次寫入
        batch.commit()
        
        logger.info(f"所有 S&P 500 成分股資料已成功寫入 Firestore！")

    except Exception as e:
        logger.error(f"寫入資料到 Firestore 時發生錯誤: {e}")

if __name__ == '__main__':
    update_sp500_sectors_in_firestore()

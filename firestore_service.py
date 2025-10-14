
import os
from google.cloud import firestore
from datetime import datetime

# --- 憑證除錯 ---
print("--- 正在進行憑證除錯 ---")
cred_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
if cred_path:
    print(f"環境變數 GOOGLE_APPLICATION_CREDENTIALS 的值是: {cred_path}")
    if os.path.exists(cred_path):
        print("✅ 檔案存在於上述路徑。")
    else:
        print("❌ 錯誤：檔案在上述路徑中不存在！請檢查路徑是否拼寫正確。")
else:
    print("❌ 錯誤：在目前的執行環境中找不到 GOOGLE_APPLICATION_CREDENTIALS 環境變數。")
    print("   可能原因：")
    print("   1. 您設定變數後，沒有重新啟動您的終端機或IDE (例如 VSCode)。")
    print("   2. 您使用的指令是 'set' 而不是 'setx'，這只對當前視窗有效。")
print("--- 除錯結束 ---\n")
# --- 憑證除錯結束 ---


# 初始化 Firestore Client
# 函式庫會自動使用 GOOGLE_APPLICATION_CREDENTIALS 環境變數來取得憑證
try:
    db = firestore.Client(project='industryweekly')
    print("Firestore client initialized successfully.")
except Exception as e:
    print(f"Error initializing Firestore client: {e}")
    print("Please ensure you have set the GOOGLE_APPLICATION_CREDENTIALS environment variable correctly.")
    db = None

def save_report(industry_name: str, report_data: dict):
    """
    將報告儲存到 Firestore。

    Args:
        industry_name (str): 產業名稱，例如 "半導體".
        report_data (dict): 包含報告內容的字典。
    """
    if not db:
        print("Firestore client is not available. Cannot save report.")
        return

    try:
        # 集合名稱
        collection_name = "industry_reports"
        
        # 使用產業名稱和日期作為文件 ID，確保唯一性
        document_id = f"{industry_name}_{datetime.utcnow().strftime('%Y-%m-%d')}"
        
        # 在報告資料中加入產業名稱和生成時間戳
        report_data['industry_name'] = industry_name
        report_data['generated_at'] = datetime.utcnow()
        
        # 取得文件參考並設定資料
        doc_ref = db.collection(collection_name).document(document_id)
        doc_ref.set(report_data)
        
        print(f"Successfully saved report to Firestore with document ID: {document_id}")
        return document_id
    except Exception as e:
        print(f"An error occurred while saving the report to Firestore: {e}")
        return None

def get_latest_report(industry_name: str):
    """
    從 Firestore 取得指定產業的最新報告。

    Args:
        industry_name (str): 產業名稱。

    Returns:
        dict: 最新的報告內容，如果找不到則返回 None。
    """
    if not db:
        print("Firestore client is not available. Cannot get report.")
        return None
        
    try:
        collection_name = "industry_reports"
        
        # 建立查詢
        query = db.collection(collection_name) \
                  .where('industry_name', '==', industry_name) \
                  .order_by('generated_at', direction=firestore.Query.DESCENDING) \
                  .limit(1)
                  
        results = query.stream()
        
        # 取得查詢結果的第一個
        for doc in results:
            print(f"Found latest report with ID: {doc.id}")
            return doc.to_dict()
            
        print(f"No report found for industry: {industry_name}")
        return None
    except Exception as e:
        print(f"An error occurred while fetching the report from Firestore: {e}")
        return None

# --- Example Usage (for testing this file directly) ---
if __name__ == '__main__':
    # 這是為了能單獨測試此檔案的功能
    print("Running Firestore service test...")
    
    # 測試儲存
    mock_report = {
        "title": "測試產業週報",
        "summary": "這是一個測試摘要。",
        "content": "這是詳細的測試內容。"
    }
    test_industry = "測試產業"
    
    saved_id = save_report(test_industry, mock_report)
    
    # 測試讀取
    if saved_id:
        latest_report = get_latest_report(test_industry)
        if latest_report:
            print("\n--- Fetched Report ---")
            print(f"Industry: {latest_report.get('industry_name')}")
            print(f"Title: {latest_report.get('title')}")
            print(f"Generated At: {latest_report.get('generated_at')}")
            print("----------------------\n")


import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import firestore
from dotenv import load_dotenv

from firestore_service import get_latest_report

# --- 初始化 ---
load_dotenv()
app = FastAPI()
logger = logging.getLogger(__name__)

# --- CORS 中介軟體設定 ---
# 允許您的 React 前端 (通常在 http://localhost:3000 或類似位址) 存取此 API
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5173", # Vite 的預設埠號
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Firestore 客戶端 ---
db = None
try:
    cred_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if cred_path and os.path.exists(cred_path):
        db = firestore.Client()
        logger.info("Firestore client initialized successfully.")
    else:
        logger.error("GOOGLE_APPLICATION_CREDENTIALS path is invalid or not set.")
except Exception as e:
    logger.error(f"Error initializing Firestore client: {e}")

# --- API 路由 ---
@app.get("/api/industry-data")
async def get_all_industry_data():
    """
    從 Firestore 的 'industry_data' 集合中獲取所有文件。
    """
    if not db:
        return {"error": "Firestore client is not available."}

    try:
        collection_ref = db.collection('industry_data')
        docs = collection_ref.stream()
        
        data = []
        for doc in docs:
            doc_data = doc.to_dict()
            # 確保 pe_history 存在且不為空
            # pe_today = None
            # if doc_data.get('pe_history') and len(doc_data['pe_history']) > 0:
            #     pe_today = doc_data['pe_history'][0].get('pe')

            data.append({
                "industry_name": doc.id,
                "pe_today": doc_data.get('pe_today'),
                "preview_summary": doc_data.get('preview_summary', ''),
                "top_stocks": doc_data.get('top_stocks', []),
                "etf_roi": doc_data.get('etf_roi') # 新增 ETF ROI 資料
            })
            
        return {"data": data}
    except Exception as e:
        logger.error(f"An error occurred while fetching data from Firestore: {e}")
        return {"error": str(e)}

@app.get("/api/industry-reports/{industry_name}/latest")
async def get_latest_industry_report(industry_name: str):
    """
    從 Firestore 的 'industry_reports' 集合中，根據產業名稱獲取最新的報告。
    """
    if not db:
        raise HTTPException(status_code=503, detail="Firestore client is not available.")

    try:
        report = get_latest_report(industry_name)
        if not report:
            raise HTTPException(status_code=404, detail=f"No report found for industry '{industry_name}'.")
        
        return report
    except Exception as e:
        logger.error(f"An error occurred while fetching the latest report for {industry_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/industry-reports/{industry_name}/{report_date}")
async def get_single_industry_report(industry_name: str, report_date: str):
    """
    從 Firestore 的 'industry_reports' 集合中，根據產業名稱和日期獲取特定報告。
    """
    if not db:
        raise HTTPException(status_code=503, detail="Firestore client is not available.")

    try:
        document_id = f"{industry_name}_{report_date}"
        doc_ref = db.collection('industry_reports').document(document_id)
        doc = doc_ref.get()

        if not doc.exists:
            raise HTTPException(status_code=404, detail=f"Report for industry '{industry_name}' on date '{report_date}' not found.")
        
        return doc.to_dict()
    except Exception as e:
        logger.error(f"An error occurred while fetching report for {industry_name} on {report_date}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"message": "Industry data API is running."}

# --- 執行 (用於本地開發) ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import firestore
from dotenv import load_dotenv
from datetime import datetime

from firestore_service import get_latest_report

load_dotenv()
app = FastAPI()
logger = logging.getLogger(__name__)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Firestore 客戶端 ---
import json
from google.oauth2 import service_account

db = None
initialization_error = None

try:
    # GOOGLE_APPLICATION_CREDENTIALS 環境變數會指向由 Zeabur 掛載的憑證檔案
    # firestore.Client() 會自動找到並使用這個環境變數
    db = firestore.Client()
    logger.info("Firestore client initialized successfully.")

except Exception as e:
    initialization_error = str(e)
    logger.error(f"A critical error occurred during Firestore client initialization: {e}")

from fastapi.staticfiles import StaticFiles

# --- API 路由 ---
@app.get("/")
async def read_root():
    return {"message": "Welcome to the Industry Weekly API!"}

@app.get("/api/industry-data")
async def get_all_industry_data():
    """
    從 Firestore 的 'industry_data' 集合中獲取所有文件。
    """
    if not db:
        error_message = "Firestore client is not available."
        if initialization_error:
            # 將捕獲到的具體錯誤訊息回傳給前端，方便除錯
            error_message += f" Reason: {initialization_error}"
        raise HTTPException(status_code=503)

    try:
        collection_ref = db.collection('industry_data')
        docs = collection_ref.stream()
        
        data = []
        for doc in docs:
            doc_data = doc.to_dict()

            data.append({
                "industry_name": doc.id,
                "pe_today": doc_data.get('pe_today'),
                "preview_summary": doc_data.get('preview_summary', ''),
                "top_stocks": doc_data.get('top_stocks', []),
                "etf_roi": doc_data.get('etf_roi'),
                "pe_high_1y": doc_data.get('pe_high_1y'),
                "pe_low_1y": doc_data.get('pe_low_1y'),
                "market_breadth_200d": round(doc_data.get('market_breadth_200d'), 1) if isinstance(doc_data.get('market_breadth_200d'), (int, float)) else doc_data.get('market_breadth_200d')
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
        raise HTTPException(status_code=503)

    try:
        report = get_latest_report(db, industry_name)
        if not report:
            raise HTTPException(status_code=404, detail=f"No report found for industry '{industry_name}'.")

        if 'generated_at' in report and report['generated_at']:
            date_val = report['generated_at']
            dt_obj = None
            try:
                if hasattr(date_val, 'isoformat'):
                    dt_obj = date_val
                elif isinstance(date_val, str) and '年' in date_val:
                    s = date_val.replace('年', '-').replace('月', '-').replace('日', '')
                    parts = s.split(' ')
                    date_part = parts[0]
                    ampm_part = parts[1]
                    time_part = parts[2]
                    parsed_dt = datetime.strptime(f"{date_part} {time_part}", '%Y-%m-%d %H:%M:%S.%f')
                    if ampm_part == '下午' and parsed_dt.hour < 12:
                        parsed_dt = parsed_dt.replace(hour=parsed_dt.hour + 12)
                    dt_obj = parsed_dt
                
                report['generated_at'] = dt_obj.isoformat() if dt_obj else None
            except (ValueError, IndexError, TypeError) as e:
                logger.warning(f"Could not parse date '{date_val}': {e}")
                report['generated_at'] = None
        else:
            report['generated_at'] = None

        return report
    except Exception as e:
        logger.error(f"An error occurred while fetching the latest report for {industry_name}: {e}")
        raise HTTPException(status_code=500)


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
        raise HTTPException(status_code=500)

if __name__ == "__main__":
    import uvicorn
    import os
    # Read the port from the PORT environment variable, with a default of 8080
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("api_server:app", host="0.0.0.0", port=port, reload=True)
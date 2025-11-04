import os
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
from datetime import datetime

# Firestore client will be passed in from api_server.py

try:
    db = firestore.Client(project='industryweekly')
    print("Firestore client initialized successfully.")
except Exception as e:
    print(f"Error initializing Firestore client: {e}")
    print("Please ensure you have set the GOOGLE_APPLICATION_CREDENTIALS environment variable correctly.")
    db = None

def save_report(report_data: dict):
    """
    將報告儲存到 Firestore。

    Args:
        db (firestore.Client): The Firestore client instance.
        report_data (dict): 包含報告內容且必須含有 'industry_name' 鍵的字典。
    """
    try:
        collection_name = "industry_reports"
        industry_name = report_data.get('industry_name', 'unknown_industry')
        document_id = f"{industry_name}_{datetime.utcnow().strftime('%Y-%m-%d')}"
        
        report_data['generated_at'] = datetime.utcnow()
        
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
    try:
        collection_name = "industry_reports"
        
        query = db.collection(collection_name) \
                  .where(filter=FieldFilter('industry_name', '==', industry_name)) \
                  .order_by('generated_at', direction=firestore.Query.DESCENDING) \
                  .limit(1)
                  
        results = query.stream()
        
        for doc in results:
            print(f"Found latest report with ID: {doc.id}")
            return doc.to_dict()
            
        print(f"No report found for industry: {industry_name}")
        return None
    except Exception as e:
        print(f"An error occurred while fetching the report from Firestore: {e}")
        return None
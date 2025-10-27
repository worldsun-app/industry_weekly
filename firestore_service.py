import os
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
from datetime import datetime

# Firestore client will be passed in from api_server.py

def save_report(db: firestore.Client, report_data: dict):
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

def get_latest_report(db: firestore.Client, industry_name: str):
    """
    從 Firestore 取得指定產業的最新報告。

    Args:
        db (firestore.Client): The Firestore client instance.
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

def save_industry_data(db: firestore.Client, industry_name: str, data: dict):
    """
    將產業數據（如 PE 歷史）儲存或合併到 Firestore 的 'industry_data' 集合中。

    Args:
        db (firestore.Client): The Firestore client instance.
        industry_name (str): 產業名稱，將作為文件 ID。
        data (dict): 要儲存的數據。
    """
    try:
        collection_name = "industry_data"
        doc_ref = db.collection(collection_name).document(industry_name)
        doc_ref.set(data, merge=True) 
        print(f"Successfully saved/merged data for '{industry_name}' in '{collection_name}'.")
    except Exception as e:
        print(f"An error occurred while saving industry data to Firestore: {e}")
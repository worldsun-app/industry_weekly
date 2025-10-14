from fmp_client import FMPClient
from report_generator import ReportGenerator
from firestore_service import save_report
import os
import datetime
import logging
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Main:
    def __init__(self):
        self.fmp_client = FMPClient(api_key=os.getenv('FMP_API_KEY'))
        google_api_key = os.getenv('GENAI_API_KEY')
        open_ai_api_key = os.getenv('OPEN_AI_API')
        self.report_generator = ReportGenerator(api_key=google_api_key, open_ai_api_key=open_ai_api_key)

    def process_main(self):
        print("開始執行產業週報生成專案...")

        # --- 1. 從 FMP 獲取產業列表 ---
        sectors = self.fmp_client.get_available_sectors()
        if not sectors:
            print("無法獲取產業列表，程式終止。")
            return

        print(f"成功獲取 {len(sectors)} 個產業。")
        print(sectors)
        pr_snapshot: list[dict] = []
        today = datetime.date.today()
        # for i in range(7):
        #     past_date = today - datetime.timedelta(days=i)
            # sector_data = self.fmp_client.get_sector_pe_snapshot(past_date)
            # if sector_data:
            #     pr_snapshot.append(sector_data)
        # print(pr_snapshot)
        
        # 只處理前3個產業作為範例，以免執行時間過長
        sectors_to_process = sectors[:1]

        # --- 2. 遍歷每個產業，收集資訊並生成報告 ---
        for sector in sectors_to_process:
            print(f"\n----------------------------------------")
            print(f"正在處理產業: {sector}")
            print(f"----------------------------------------")
            json_data = self.report_generator.generate_industry_events(sector, today)
            print(json_data)
            report_data = self.report_generator.generate_weekly_report(sector, today, json_data)
            # 從回傳的字典中取得報告全文來印出
            full_report = report_data.get('full_report_text', '')
            print(f"\n生成的週報:\n{full_report}")

            # --- 新增：將報告拆分為兩部分 ---
            part1_header = "第一部分 整體趨勢概述"
            part2_header = "第二部分 主題趨勢分析"
            
            part1_start = full_report.find(part1_header)
            part2_start = full_report.find(part2_header)
            
            report_part_1 = ""
            report_part_2 = ""
            
            if part1_start != -1 and part2_start != -1:
                report_part_1 = full_report[part1_start + len(part1_header):part2_start].strip()
                report_part_2 = full_report[part2_start:].strip()
            elif part1_start != -1:
                report_part_1 = full_report[part1_start + len(part1_header):].strip()

            # 更新 report_data 字典
            report_data['report_part_1'] = report_part_1
            report_data['report_part_2'] = report_part_2
            report_data.pop('full_report_text', None)  # 移除舊的完整報告欄位
            # 將產出的報告儲存到 Firestore
            logger.info(f"準備將 '{sector}' 的報告儲存至 Firestore...")
            save_report(industry_name=sector, report_data=report_data)

if __name__ == '__main__':
    main_app = Main()
    main_app.process_main()
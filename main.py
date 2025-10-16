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
        sectors_to_process = sectors[:]

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

            # --- 新的拆分邏輯 ---
            # 以換行符分割報告為多個段落
            paragraphs = full_report.strip().split('\n\n')
            
            # 過濾掉空段落
            paragraphs = [p.strip() for p in paragraphs if p.strip()]
            
            report_part_1 = ""
            report_part_2 = ""

            if len(paragraphs) > 1:
                # 根據新的 prompt，第一段是標題，所以報告內容從第二段開始
                # report_part_1 對應 prompt 中的 "段落一"
                report_part_1 = paragraphs[1]
                
                # report_part_2 是從第三段開始的所有內容
                if len(paragraphs) > 2:
                    report_part_2 = '\n\n'.join(paragraphs[2:])
            # --- 拆分結束 ---

            # 更新 report_data 字典
            report_data['report_part_1'] = report_part_1
            report_data['report_part_2'] = report_part_2
            report_data.pop('full_report_text', None)  # 移除舊的完整報告欄位

            # --- 新增：生成預覽摘要 ---
            if report_part_1:
                logger.info("正在生成預覽摘要...")
                preview_summary = self.report_generator.generate_preview_summary(report_part_1)
                report_data['preview_summary'] = preview_summary
                print(f"\n生成的預覽摘要: {preview_summary}")
            else:
                report_data['preview_summary'] = "" # or some default text
            # --- 摘要結束 ---

            # 將產業名稱加入字典，並呼叫已更新的儲存函式
            report_data['industry_name'] = sector['sector']
            logger.info(f"準備將 '{sector}' 的報告儲存至 Firestore...")
            save_report(report_data=report_data)

if __name__ == '__main__':
    main_app = Main()
    main_app.process_main()
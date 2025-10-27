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
        today = datetime.date.today()
        sectors_to_process = sectors[:]

        # --- 2. 遍歷每個產業，收集資訊並生成報告 ---
        for sector in sectors_to_process:
            print(f"\n----------------------------------------")
            print(f"正在處理產業: {sector}")
            print(f"----------------------------------------")
            json_data = self.report_generator.generate_industry_events(sector, today)
            report_data = self.report_generator.generate_weekly_report(sector, today, json_data)
            full_report = report_data.get('full_report_text', '')

            paragraphs = full_report.strip().split('\n\n')
            paragraphs = [p.strip() for p in paragraphs if p.strip()]
            report_part_1 = ""
            report_part_2 = ""

            if len(paragraphs) > 1:
                report_part_1 = paragraphs[1]
                if len(paragraphs) > 2:
                    report_part_2 = '\n\n'.join(paragraphs[2:])
            report_data['report_part_1'] = report_part_1
            report_data['report_part_2'] = report_part_2
            report_data.pop('full_report_text', None)

            if report_part_1:
                logger.info("正在生成預覽摘要...")
                preview_summary = self.report_generator.generate_preview_summary(report_part_1)
                report_data['preview_summary'] = preview_summary
                print(f"\n生成的預覽摘要: {preview_summary}")
            else:
                report_data['preview_summary'] = ""

            report_data['industry_name'] = sector['sector']
            logger.info(f"準備將 '{sector}' 的報告儲存至 Firestore...")
            save_report(report_data=report_data)
            print(f"完成產業 '{sector}' 的報告生成與儲存。")

def run_main():
    main_app = Main()
    main_app.process_main()

if __name__ == '__main__':
    run_main()

from datetime import datetime
import logging

from google import genai
from google.genai import types
from google.genai.types import GenerateContentConfig
from google.protobuf.struct_pb2 import Struct
from google.genai import errors as genai_errors

from openai import OpenAI

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def _load_prompt_template(name: str) -> str:
    with open(f"prompts/{name}.txt", "r", encoding="utf-8") as f:
        return f.read()
    return ""

class ReportGenerator:
    def __init__(self, api_key: str, open_ai_api_key: str):
        if not api_key:
            raise ValueError("❌ 錯誤：Google API 金鑰未提供。")
        
        self.client = genai.Client(api_key=api_key)
        grounding_tool = types.Tool(google_search=types.GoogleSearch())
        self.config = types.GenerateContentConfig(tools=[grounding_tool])
        self.open_client = OpenAI(api_key=open_ai_api_key)

    def generate_industry_events(self, sector: str, date: datetime) -> str:
        template = _load_prompt_template("report_stage1")
        prompt = template.format(sector=sector, date=date)
        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=self.config
        )
        return response.text.strip()
    
    def generate_weekly_report(self, sector: str, today: datetime.date, json_data: str):
        template = _load_prompt_template("report_stage2")
        prompt = template.format(sector=sector, date=today, json_data=json_data)
        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=self.config
        )
        report_text = response.text.strip()
        logger.info("週報文字已生成，準備轉換為結構化資料。")
        report_data = {
            "title": f"{sector} 產業週報 {today.strftime('%Y-%m-%d')}",
            "full_report_text": report_text,
            "source_events_json": json_data,
        }
        return report_data

    def generate_preview_summary(self, report_part_1_text: str) -> str:
        template = _load_prompt_template("summarize_for_preview")
        prompt = template.format(report_part_1_text=report_part_1_text)
        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=self.config
        )
        report_text = response.text.strip()
        logger.info("週報文字已生成，準備轉換為結構化資料。")

        return report_text
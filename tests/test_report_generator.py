
import unittest
from unittest.mock import patch, MagicMock
import os
import datetime

# Add the parent directory to the path so that we can import the report_generator module
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from report_generator import ReportGenerator

class TestReportGenerator(unittest.TestCase):

    @patch('report_generator.genai.Client')
    @patch('report_generator.OpenAI')
    def setUp(self, mock_openai, mock_genai_client):
        """Set up the test environment before each test."""
        self.mock_genai_client = mock_genai_client
        self.mock_openai_client = mock_openai

        # Instantiate the ReportGenerator with mock clients
        self.report_generator = ReportGenerator(api_key='fake_google_api_key', open_ai_api_key='fake_openai_api_key')
        self.report_generator.client = self.mock_genai_client
        self.report_generator.open_client = self.mock_openai_client

    def test_generate_industry_events(self):
        """Test the generate_industry_events method."""
        # Configure the mock to return a specific value
        mock_response = MagicMock()
        mock_response.text = 'Mocked industry events'
        self.mock_genai_client.models.generate_content.return_value = mock_response

        # Call the method to be tested
        sector = 'Technology'
        date = datetime.date(2025, 10, 27)
        result = self.report_generator.generate_industry_events(sector, date)

        # Assert that the mock was called with the correct parameters
        self.mock_genai_client.models.generate_content.assert_called_once()
        # You can add more specific assertions about the call arguments if needed

        # Assert that the result is as expected
        self.assertEqual(result, 'Mocked industry events')

    def test_generate_weekly_report(self):
        """Test the generate_weekly_report method."""
        # Configure the mock to return a specific value
        mock_response = MagicMock()
        mock_response.text = 'Mocked weekly report'
        self.mock_genai_client.models.generate_content.return_value = mock_response

        # Call the method to be tested
        sector = 'Healthcare'
        today = datetime.date(2025, 10, 27)
        json_data = '{"event": "Mock event"}'
        result = self.report_generator.generate_weekly_report(sector, today, json_data)

        # Assert that the mock was called with the correct parameters
        self.mock_genai_client.models.generate_content.assert_called_once()

        # Assert that the result is as expected
        expected_result = {
            'title': f'{sector} 產業週報 {today.strftime("%Y-%m-%d")}',
            'full_report_text': 'Mocked weekly report',
            'source_events_json': json_data,
        }
        self.assertEqual(result, expected_result)

    def test_generate_preview_summary(self):
        """Test the generate_preview_summary method."""
        # Configure the mock to return a specific value
        mock_response = MagicMock()
        mock_response.text = 'Mocked preview summary'
        self.mock_genai_client.models.generate_content.return_value = mock_response

        # Call the method to be tested
        report_part_1_text = 'This is the first part of the report.'
        result = self.report_generator.generate_preview_summary(report_part_1_text)

        # Assert that the mock was called with the correct parameters
        self.mock_genai_client.models.generate_content.assert_called_once()

        # Assert that the result is as expected
        self.assertEqual(result, 'Mocked preview summary')

if __name__ == '__main__':
    unittest.main()

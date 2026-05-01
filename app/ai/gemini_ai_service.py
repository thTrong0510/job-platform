from google import genai
from google.genai import types

from app.ai.prompt_templates import CV_EXTRACTION_PROMPT
from app.ai.schemas import CVExtractForProfile


class GeminiAIService:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.model_id = "gemini-2.5-flash"

    def extract_cv_data(self, file_path: str) -> CVExtractForProfile:
        prompt = CV_EXTRACTION_PROMPT
        uploaded_file = self.client.files.upload(file=file_path)

        response = self.client.models.generate_content(
            model=self.model_id,
            contents = [prompt, uploaded_file],
            config = types.GenerateContentConfig(
                temperature=0.0,
                response_mime_type="application/json",
                response_schema = CVExtractForProfile
            )
        )
        return response.parsed


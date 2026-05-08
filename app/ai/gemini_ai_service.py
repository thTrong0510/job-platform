import httpx
from google import genai
from google.genai import types

from app.ai.prompt_templates import CV_EXTRACTION_PROMPT
from app.ai.schemas import CVExtractForProfile

MIME_MAP = {
    "pdf":  "application/pdf",
    "doc":  "application/msword",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

class GeminiAIService:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.model_id = "gemini-2.5-flash"

    def extract_cv_from_bytes(self, file_bytes: bytes, filename: str) -> CVExtractForProfile:
        """Khi user upload file mới, đọc từ bytes trong memory"""
        ext = filename.rsplit(".", 1)[-1].lower()
        mime_type = MIME_MAP.get(ext, "application/pdf")
        part = types.Part.from_bytes(data=file_bytes, mime_type=mime_type)

        response = self.client.models.generate_content(
            model=self.model_id,
            contents = [CV_EXTRACTION_PROMPT, part],
            config = types.GenerateContentConfig(
                temperature=0.0,
                response_mime_type="application/json",
                response_schema = CVExtractForProfile
            )
        )
        return response.parsed

    def extract_cv_from_image_url(self, img_url: str) -> CVExtractForProfile:
        """Khi cv lưu dạng JPG"""
        img_bytes = httpx.get(img_url).content
        img_part = types.Part.from_bytes(
            data = img_bytes,
            mime_type = "image/jpeg"
        )
        response = self.client.models.generate_content(
            model = self.model_id,
            contents = [CV_EXTRACTION_PROMPT, img_part],
            config = types.GenerateContentConfig(
                temperature=0.0,
                response_mime_type="application/json",
                response_schema = CVExtractForProfile
            )
        )
        return response.parsed


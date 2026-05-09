import httpx
import time
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
        """Xử lý ảnh CV với cơ chế Retry và Tối ưu hóa chất lượng ảnh"""

        # 1. Tối ưu URL Cloudinary (Nếu có thể)
        # Thêm tham số để lấy ảnh chất lượng cao nhất, loại bỏ nén mất dữ liệu
        optimized_url = img_url
        if "cloudinary.com" in img_url:
            # Ép Cloudinary trả về ảnh chất lượng cao và định dạng rõ ràng
            optimized_url = img_url.replace("/upload/", "/upload/q_auto:best,f_jpg/")

        try:
            # 2. Lấy dữ liệu ảnh với Timeout để tránh treo server
            response_img = httpx.get(optimized_url, timeout=20.0)
            response_img.raise_for_status()
            img_bytes = response_img.content

            img_part = types.Part.from_bytes(
                data=img_bytes,
                mime_type="image/jpeg"
            )

            # 3. Cơ chế Retry để đối phó với lỗi Location/Internal Error
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self.client.models.generate_content(
                        model=self.model_id,
                        contents=[
                            # Cải thiện Prompt: Yêu cầu AI đọc thật kỹ (OCR-focused)
                            "Hãy đóng vai trò là một chuyên gia nhân sự. "
                            "Nhiệm vụ của bạn là đọc bản scan/ảnh CV sau đây và trích xuất dữ liệu "
                            "chính xác 100%, không bỏ sót các chi tiết về kỹ năng và kinh nghiệm."
                            "Trích xuất phần Bio ngắn gọn trong khoảng 200 ký tự. lưu ý chỉ trích xuất ngắn gọn khi bạn cho rằng lượng token sử dụng có thể bị vượt ngưỡng 10000",
                            img_part
                        ],
                        config=types.GenerateContentConfig(
                            temperature=0.1,  # Tăng nhẹ để model linh hoạt hơn nếu 0.0 quá cứng nhắc
                            response_mime_type="application/json",
                            response_schema=CVExtractForProfile,
                            # Tăng cường độ ưu tiên cho thị giác
                            max_output_tokens=10000
                        )
                    )

                    if response.parsed is None:
                        # Nếu không parse được theo schema, in ra nội dung thô để xem AI đang trả về gì
                        print(f"--- RAW RESPONSE CONTENT: {response.text} ---")
                        raise ValueError("File CV của bạn có quá nhiều dữ liệu vượt quá ngưỡng cho phép phân tích.")
                    return response.parsed

                except Exception as e:
                    # In ra toàn bộ lỗi để bạn check trong Logs của Render
                    print(f"--- DEBUG ERROR TYPE: {type(e)} ---")
                    print(f"--- DEBUG ERROR MSG: {str(e)} ---")
                    # Kiểm tra chính xác hơn dựa trên thuộc tính của exception (nếu có)
                    err_msg = str(e).lower()
                    is_location_error = "location" in err_msg or "supported" in err_msg
                    is_400 = "400" in err_msg
                    if is_location_error or is_400:
                        if attempt < max_retries - 1:
                            print(f"Đang thử lại lần {attempt + 1} do lỗi vùng miền/400...")
                            time.sleep(2)  # Tăng thời gian đợi lên một chút
                            continue
                    # Nếu không phải lỗi vùng miền hoặc đã hết lượt retry
                    raise e

        except httpx.HTTPStatusError as e:
            print(f"Lỗi khi tải ảnh từ Cloudinary: {e}")
            raise
        except Exception as e:
            print(f"Lỗi xử lý CV: {e}")
            raise


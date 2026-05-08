from flask import current_app
from app.ai.gemini_ai_service import GeminiAIService
from app.common.file_utils import CVFileUtils
from app.repositories.candidate.cv_repository import CVRepository


class CVExtractionService:
    @staticmethod
    def get_gemini_service():
        if not hasattr(current_app, '_gemini_service'):
            api_key = current_app.config['GEMINI_API_KEY']
            if not api_key:
                raise ValueError('GEMINI_API_KEY is not configured in app config')
            current_app._gemini_service = GeminiAIService(api_key)
        return current_app._gemini_service

    @staticmethod
    def process_extraction(candidate_id, form, files):
        cv_id = form.get('cv_id')
        file = files.get('cv_file')

        try:
            ai_service = CVExtractionService.get_gemini_service()
            if cv_id:
                """CV đã lưu → file_url là ảnh JPG trên Cloudinary"""
                cv = CVRepository.find_by_id_and_candidate(cv_id, candidate_id)
                if not cv or not cv.file_url or cv.type != "UPLOAD":
                    raise ValueError('Dữ liệu CV không hợp lệ hoặc đã bị xoá')

                result = ai_service.extract_cv_from_image_url(cv.file_url)

            elif file and file.filename:
                is_valid, msg = CVFileUtils.is_valid_size(file)
                if not is_valid:
                    raise ValueError(msg)

                if not CVFileUtils.allowed_file(file.filename):
                    raise ValueError("Chỉ hỗ trợ file PDF, DOC, DOCX")

                file_bytes = file.read()
                result = ai_service.extract_cv_from_bytes(file_bytes, file.filename)

            else:
                raise ValueError("Vui lòng chọn CV từ danh sách hoặc tải lên tệp mới")

            return result.model_dump()
        except ValueError as error:
            raise error
        except Exception as e:
            current_app.logger.error(f"CV extraction error: {e}")
            raise RuntimeError("Hệ thống đang bận, vui lòng thử lại sau")
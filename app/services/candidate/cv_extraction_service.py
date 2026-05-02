import os

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

        full_path = None
        temp_path = None
        try:
            # Lấy path
            if cv_id:
                cv = CVRepository.find_by_id_and_candidate(cv_id, candidate_id)
                if not cv or not cv.file_url or cv.type != "UPLOAD":
                    raise ValueError('Dữ liệu CV không hợp lệ hoặc đã bị xoá')

                full_path = CVFileUtils.get_full_path(cv.file_url)
                if not full_path or not os.path.exists(full_path):
                    raise ValueError("File CV không tồn tại")

            elif file and file.filename:
                is_valid, msg = CVFileUtils.is_valid_size(file)
                if not is_valid:
                    raise ValueError(msg)

                if not CVFileUtils.allowed_file(file.filename):
                    raise ValueError("Chỉ hỗ trợ file PDF, DOC, DOCX")

                temp_path = CVFileUtils.save_temp(file)
                full_path = temp_path

            else:
                raise ValueError("Vui lòng chọn CV từ danh sách hoặc tải lên tệp mới")

            # Gọi AI
            ai_service = CVExtractionService.get_gemini_service()
            result = ai_service.extract_cv_data(full_path)

            return result.model_dump()
        except ValueError as error:
            raise error
        except Exception as e:
            raise RuntimeError("Hệ thống đang bận, vui lòng thử lại sau")
        finally:
            if temp_path and os.path.exists(temp_path):
                CVFileUtils.delete_temp(temp_path)
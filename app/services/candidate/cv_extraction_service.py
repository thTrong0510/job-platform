from flask import current_app
from app.ai.gemini_ai_service import GeminiAIService
from app.ai.schemas import CVExtractForProfile
from app.common.file_utils import CVFileUtils
from app.repositories.candidate.cv_repository import CVRepository
import json
from app.ai.schemas import CVExtractForProfile, ExperienceExtract, EducationExtract


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
    def extract_from_online_cv(cv) -> CVExtractForProfile:
        data = cv.content_json
        skill_names = [item.skill.name for item in cv.skills] if cv.skills else []
        if not data:
            raise ValueError('CV trống')
        return CVExtractForProfile(
            full_name=data.get("full_name", ""),
            phone=data.get("phone"),
            location=data.get("location"),
            bio=data.get("summary"),
            current_title=data.get("current_title"),
            experiences=[
                ExperienceExtract(
                    company=e.get("company"),
                    position=e.get("position"),
                    start_date=e.get("start_date"),
                    end_date=e.get("end_date"),
                    description=e.get("description"),
                )
                for e in data.get("experiences", [])
            ],
            educations=[
                EducationExtract(
                    school=e.get("school", ""),
                    degree=e.get("degree"),
                    start_date=e.get("start_date"),
                    end_date=e.get("end_date"),
                )
                for e in data.get("educations", [])
            ],
            skills=skill_names
        )


    @staticmethod
    def process_extraction(candidate_id, form, files):
        cv_online_id = form.get('cv_online_id')
        cv_upload_id = form.get('cv_upload_id')
        cv_id = cv_online_id or cv_upload_id
        file = files.get('cv_file')

        try:
            ai_service = CVExtractionService.get_gemini_service()
            if cv_id:
                cv = CVRepository.find_by_id_and_candidate(cv_id, candidate_id)
                if not cv:
                    raise ValueError('CV không tồn tại hoặc đã bị xoá')

                if cv.type == "UPLOAD":
                    """CV đã lưu → file_url là ảnh JPG trên Cloudinary"""
                    result = ai_service.extract_cv_from_image_url(cv.file_url)

                elif cv.type == "ONLINE":
                    result = CVExtractionService.extract_from_online_cv(cv)

                else:
                    raise ValueError("Loại CV không hợp lệ")

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
        except ValueError:
            raise
        except ConnectionError:
            current_app.logger.error("Gemini connection error")
            raise RuntimeError("Không thể kết nối tới AI. Vui lòng kiểm tra lại internet.")

        except AttributeError as e:
            current_app.logger.error(f"Logic/Schema error: {e}")
            raise RuntimeError("Dữ liệu CV không tương thích với hệ thống.")

        except Exception as e:
            current_app.logger.error(f"CV extraction unexpected error: {e}")
            if current_app.debug:
                raise e
            raise RuntimeError("Có lỗi xảy ra trong quá trình đọc CV. Vui lòng thử lại.")
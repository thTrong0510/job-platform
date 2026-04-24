import os
import uuid
from werkzeug.utils import secure_filename
from app.models.cv import CV
from app.repositories.candidate.cv_upload_repository import CVUploadRepository

ALLOWED_EXTENSIONS = {"pdf", "doc", "docx"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# Đường dẫn tuyệt đối tới thư mục lưu file
UPLOAD_FOLDER = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "static", "uploads", "cvs"
)


class CVUploadService:

    @staticmethod
    def allowed_file(filename):
        return (
            "." in filename
            and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
        )

    @staticmethod
    def get_candidate(user_id):
        return CVUploadRepository.find_candidate_by_user_id(user_id)

    @staticmethod
    def get_uploaded_cvs(user_id):
        candidate = CVUploadRepository.find_candidate_by_user_id(user_id)
        if not candidate:
            return []
        return CVUploadRepository.find_cvs_by_candidate_id(candidate.id)

    @staticmethod
    def upload_cv(user_id, file, title):
        # Kiểm tra candidate tồn tại
        candidate = CVUploadRepository.find_candidate_by_user_id(user_id)
        if not candidate:
            return False, "Bạn chưa có hồ sơ ứng viên. Vui lòng tạo hồ sơ trước."

        # Kiểm tra file
        if not file or file.filename == "":
            return False, "Vui lòng chọn file để tải lên."

        if not CVUploadService.allowed_file(file.filename):
            return False, "Định dạng file không hợp lệ. Chỉ chấp nhận .pdf, .doc, .docx."

        # Kiểm tra kích thước file
        file.seek(0, 2)
        file_size = file.tell()
        file.seek(0)

        if file_size > MAX_FILE_SIZE:
            return False, "Kích thước file vượt quá 5MB."

        # Tạo folder nếu chưa có
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)

        # Tạo tên file unique để tránh trùng lặp
        original_filename = secure_filename(file.filename)
        ext = original_filename.rsplit(".", 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{ext}"

        save_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(save_path)

        file_url = f"/static/uploads/cvs/{unique_filename}"
        cv_title = title.strip() if title and title.strip() else original_filename

        cv = CV(
            candidate_id=candidate.id,
            title=cv_title,
            type="UPLOAD",
            file_url=file_url,
            file_name=original_filename,
            file_size=file_size,
        )

        CVUploadRepository.save_cv(cv)
        return True, "Tải lên CV thành công!"

    @staticmethod
    def delete_cv(user_id, cv_id):
        candidate = CVUploadRepository.find_candidate_by_user_id(user_id)
        if not candidate:
            return False, "Không tìm thấy hồ sơ ứng viên."

        cv = CVUploadRepository.find_cv_by_id(cv_id)

        # Kiểm tra CV tồn tại và thuộc về candidate này
        if not cv or cv.candidate_id != candidate.id:
            return False, "Không tìm thấy CV hoặc bạn không có quyền xóa."

        # Xóa file vật lý
        physical_path = os.path.join(UPLOAD_FOLDER, os.path.basename(cv.file_url))
        if os.path.exists(physical_path):
            os.remove(physical_path)

        CVUploadRepository.delete_cv(cv)
        return True, "Đã xóa CV thành công."
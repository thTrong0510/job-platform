import os
import uuid
from flask import current_app
from werkzeug.utils import secure_filename

TEMP_FOLDER = "app/static/uploads/cv_temp"
ALLOWED_EXTENSIONS = {"pdf", "doc", "docx"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


class CVFileUtils:

    @staticmethod
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    @staticmethod
    def is_valid_size(file):
        file.seek(0, 2)
        file_size = file.tell()
        file.seek(0)

        if file_size > MAX_FILE_SIZE:
            return False, "Kích thước file vượt quá 5MB."
        return True, ""

    @staticmethod
    def get_full_path(file_url: str) -> str:
        relative_path = file_url.replace("\\", "/").lstrip("/")
        return os.path.join(current_app.root_path, relative_path)

    @staticmethod
    def save_temp(file):
        if not os.path.exists(TEMP_FOLDER):
            os.makedirs(TEMP_FOLDER)

        file_name = secure_filename(file.filename)
        unique_name = f"{uuid.uuid4().hex}_{file_name}"
        temp_path = os.path.join(TEMP_FOLDER, unique_name)
        file.save(temp_path)
        return temp_path

    @staticmethod
    def delete_temp(file_path):
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
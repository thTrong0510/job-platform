"""
app/services/employer/cv_text_extractor.py

Trích xuất raw text từ CV để phục vụ matching với Gemini.
- CV ONLINE  : đọc trực tiếp từ content_json (không cần file)
- CV UPLOAD  : extract text từ file PDF (pdfplumber) / DOCX (python-docx)
"""
import os


# Đường dẫn tuyệt đối đến thư mục lưu file upload — khớp với cv_upload_service.py
_UPLOAD_FOLDER = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "static", "uploads", "cvs"
)


class CVTextExtractor:

    @staticmethod
    def extract(cv) -> str:
        """Entry point: trả về toàn bộ text của CV dưới dạng string thuần."""
        if cv.type == "ONLINE":
            return CVTextExtractor._from_json(cv)
        if cv.type == "UPLOAD":
            return CVTextExtractor._from_file(cv)
        return ""

    # ─────────────────────────────────────────────────────────
    # CV ONLINE — đọc từ content_json
    # ─────────────────────────────────────────────────────────
    @staticmethod
    def _from_json(cv) -> str:
        data = cv.content_json
        if not data:
            return ""

        parts = []

        # Thông tin cơ bản
        for field in ("full_name", "phone", "location", "email"):
            if data.get(field):
                parts.append(str(data[field]))

        # Tóm tắt bản thân
        if data.get("summary"):
            parts.append(data["summary"])

        # Kinh nghiệm làm việc
        for exp in data.get("experiences", []):
            line = " ".join(filter(None, [
                exp.get("position", ""),
                "tại" if exp.get("company") else "",
                exp.get("company", ""),
                exp.get("description", ""),
            ]))
            if line.strip():
                parts.append(line)

        # Học vấn
        for edu in data.get("educations", []):
            line = " ".join(filter(None, [
                edu.get("degree", ""),
                "tại" if edu.get("school") else "",
                edu.get("school", ""),
            ]))
            if line.strip():
                parts.append(line)

        # Dự án
        for proj in data.get("projects", []):
            line = " ".join(filter(None, [
                proj.get("name", ""),
                proj.get("description", ""),
            ]))
            if line.strip():
                parts.append(line)

        return "\n".join(parts)

    # ─────────────────────────────────────────────────────────
    # CV UPLOAD — extract text từ file vật lý
    # ─────────────────────────────────────────────────────────
    @staticmethod
    def _from_file(cv) -> str:
        if not cv.file_url:
            return ""

        filename = os.path.basename(cv.file_url)
        filepath = os.path.join(_UPLOAD_FOLDER, filename)

        if not os.path.exists(filepath):
            return ""

        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        if ext == "pdf":
            return CVTextExtractor._pdf(filepath)
        if ext == "docx":
            return CVTextExtractor._docx(filepath)

        # .doc hoặc định dạng khác — không extract được, trả rỗng
        return ""

    @staticmethod
    def _pdf(filepath: str) -> str:
        try:
            import pdfplumber
            pages = []
            with pdfplumber.open(filepath) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        pages.append(text)
            return "\n".join(pages)
        except Exception as e:
            print(f"[CVTextExtractor] PDF extract error: {e}")
            return ""

    @staticmethod
    def _docx(filepath: str) -> str:
        try:
            from docx import Document
            doc = Document(filepath)
            return "\n".join(
                p.text for p in doc.paragraphs if p.text.strip()
            )
        except Exception as e:
            print(f"[CVTextExtractor] DOCX extract error: {e}")
            return ""
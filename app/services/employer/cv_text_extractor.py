"""
Trích xuất nội dung CV để phục vụ matching với Gemini.

- CV ONLINE  : đọc trực tiếp từ content_json → trả về text thuần.
- CV UPLOAD  : file lưu trên Cloudinary dạng JPG
               → trả về URL để matching_service gọi Gemini Vision.
"""

_CLOUDINARY_PREFIX = "https://res.cloudinary.com"


class CVTextExtractor:

    @staticmethod
    def extract(cv) -> str:
        """
        Trả về text thuần cho CV ONLINE.
        Với CV UPLOAD (Cloudinary) → trả về "" vì
        matching_service sẽ gọi Gemini Vision bằng URL ảnh.
        """
        if cv.type == "ONLINE":
            return CVTextExtractor._from_json(cv)
        # UPLOAD → không extract text, dùng Vision
        return ""

    @staticmethod
    def is_cloudinary_image(cv) -> bool:
        """True nếu CV UPLOAD lưu trên Cloudinary."""
        return (
            cv.type == "UPLOAD"
            and bool(cv.file_url)
            and cv.file_url.startswith(_CLOUDINARY_PREFIX)
        )

    @staticmethod
    def get_cloudinary_url(cv) -> str | None:
        """Trả về URL Cloudinary, hoặc None nếu không phải."""
        if CVTextExtractor.is_cloudinary_image(cv):
            return cv.file_url
        return None

    # ─────────────────────────────────────────────────────────
    # CV ONLINE — đọc từ content_json
    # ─────────────────────────────────────────────────────────
    @staticmethod
    def _from_json(cv) -> str:
        data = cv.content_json
        if not data:
            return ""

        parts = []

        for field in ("full_name", "phone", "location", "email"):
            if data.get(field):
                parts.append(str(data[field]))

        if data.get("summary"):
            parts.append(data["summary"])

        for exp in data.get("experiences", []):
            line = " ".join(filter(None, [
                exp.get("position", ""),
                "tại" if exp.get("company") else "",
                exp.get("company", ""),
                exp.get("description", ""),
            ]))
            if line.strip():
                parts.append(line)

        for edu in data.get("educations", []):
            line = " ".join(filter(None, [
                edu.get("degree", ""),
                "tại" if edu.get("school") else "",
                edu.get("school", ""),
            ]))
            if line.strip():
                parts.append(line)

        for proj in data.get("projects", []):
            line = " ".join(filter(None, [
                proj.get("name", ""),
                proj.get("description", ""),
            ]))
            if line.strip():
                parts.append(line)

        return "\n".join(parts)
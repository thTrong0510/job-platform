"""
Tính điểm phù hợp giữa CV ứng viên và Job Description bằng Gemini API.

Luồng:
  1. Kiểm tra DB (job_recommendations) — nếu đã có score thì dùng lại.
  2. Nếu chưa có:
     - CV ONLINE / UPLOAD local  → extract text → gọi Gemini text prompt.
     - CV UPLOAD Cloudinary (JPG) → gọi Gemini Vision (image + text prompt).
  3. Lưu score vào DB.
"""
import os
import re

from app.extensions import db
from app.models.recommendation import JobRecommendation
from app.repositories.candidate.cv_skill_repository import CVSkillRepository
from app.repositories.candidate.skill_repository import SkillRepository
from app.services.employer.cv_text_extractor import CVTextExtractor
from app.repositories.employer.recommend_job_repository import RecommendJobRepository

# ── Khởi tạo Gemini client (lazy singleton) ──────────────────────
_client = None


def _get_client():
    global _client
    if _client is None:
        from google import genai
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY chưa được cấu hình trong file .env")
        _client = genai.Client(api_key=api_key)
    return _client


_GEMINI_MODEL = "gemini-2.5-flash"


# ─────────────────────────────────────────────────────────────────
class MatchingService:

    # ── Public: lấy score (cache → tính mới) ──────────────────────
    @staticmethod
    def get_or_calculate(application) -> float | None:
        cached = MatchingService._load_from_db(
            application.cv.candidate_id, application.job_id
        )
        if cached is not None:
            return cached
        return MatchingService._calculate_and_save(application)

    # ── Internal: load từ DB ──────────────────────────────────────
    @staticmethod
    def _load_from_db(candidate_id: int, job_id: int) -> float | None:
        rec = JobRecommendation.query.filter_by(
            candidate_id=candidate_id,
            job_id=job_id,
        ).first()

        if rec is None:
            RecommendJobRepository.save(candidate_id, job_id)
            return None

        if rec.score is not None:
            return float(rec.score)
        return None

    # ── Internal: xóa khỏi DB ─────────────────────────────────────
    @staticmethod
    def _delete_from_db(candidate_id: int, job_id: int):
        JobRecommendation.query.filter_by(
            candidate_id=candidate_id,
            job_id=job_id,
        ).delete()
        db.session.commit()

    # ── Internal: tính điểm → lưu DB ──────────────────────────────
    @staticmethod
    def _calculate_and_save(application) -> float | None:
        try:
            score = MatchingService._score(application)
            if score is None:
                return None

            rec = JobRecommendation.query.filter_by(
                candidate_id=application.cv.candidate_id,
                job_id=application.job_id,
            ).first()

            if rec:
                rec.score = score
            else:
                rec = JobRecommendation(
                    candidate_id=application.cv.candidate_id,
                    job_id=application.job_id,
                    score=score,
                )
                db.session.add(rec)

            db.session.commit()
            return score

        except Exception as e:
            print(f"[MatchingService] Error saving score: {e}")
            db.session.rollback()
            return None

    # ── Internal: router — text-based vs image-based ─────────────
    @staticmethod
    def _score(application) -> float | None:
        job = application.job
        cv  = application.cv

        # Thông tin bổ sung từ hồ sơ ứng viên (dùng chung cho cả 2 path)
        extra = MatchingService._build_extra_context(cv)

        # ── CV UPLOAD lưu trên Cloudinary → dùng Gemini Vision ──
        if CVTextExtractor.is_cloudinary_image(cv):
            image_url = CVTextExtractor.get_cloudinary_url(cv)
            return MatchingService._call_gemini_vision(
                job=job,
                image_url=image_url,
                extra_context=extra,
            )

        # ── CV ONLINE hoặc UPLOAD local → dùng text prompt ──────
        cv_text = CVTextExtractor.extract(cv)

        # Gắn kỹ năng + thông tin bổ sung vào cv_text
        skill_ids      = CVSkillRepository.get_skill_ids_by_cv(cv.id)
        cv_skills      = SkillRepository.get_by_ids(skill_ids)
        cv_skill_names = [s.name for s in cv_skills]
        if cv_skill_names:
            cv_text += "\nKỹ năng trong CV: " + ", ".join(cv_skill_names)

        cv_text += extra

        if not cv_text.strip():
            print(f"[MatchingService] CV #{cv.id} không có text để phân tích")
            return None

        job_skill_names = [js.skill.name for js in job.skills]
        return MatchingService._call_gemini_text(
            job_title=job.title,
            job_description=job.description or "",
            job_skills=job_skill_names,
            experience_required=job.experience_required,
            cv_text=cv_text,
        )

    # ── Internal: build extra context từ profile ứng viên ────────
    @staticmethod
    def _build_extra_context(cv) -> str:
        parts = []
        cand_skill_names = [cs.skill.name for cs in cv.candidate.skills]
        if cand_skill_names:
            parts.append("\nKỹ năng ứng viên: " + ", ".join(cand_skill_names))
        if cv.candidate.total_experience_years:
            parts.append(f"\nTổng kinh nghiệm: {cv.candidate.total_experience_years} năm")
        if cv.candidate.current_title:
            parts.append(f"\nVị trí hiện tại: {cv.candidate.current_title}")
        if cv.candidate.bio:
            parts.append(f"\nGiới thiệu: {cv.candidate.bio}")
        return "".join(parts)

    # ── Internal: Gemini Vision — CV là ảnh JPG trên Cloudinary ──
    @staticmethod
    def _call_gemini_vision(job, image_url: str, extra_context: str) -> float | None:
        """
        Gửi ảnh CV (Cloudinary URL) + mô tả job lên Gemini Vision.
        Gemini đọc ảnh, hiểu nội dung CV, rồi chấm điểm phù hợp.
        """
        try:
            import httpx
            from google.genai import types

            job_skill_names = [js.skill.name for js in job.skills]
            skill_str = ", ".join(job_skill_names) if job_skill_names else "Không có yêu cầu cụ thể"
            exp_str   = f"{job.experience_required}+ năm" if job.experience_required else "Không yêu cầu"

            prompt = f"""Bạn là chuyên gia tuyển dụng IT. Hình ảnh đính kèm là CV của ứng viên.
Hãy đọc toàn bộ nội dung CV trong ảnh, sau đó đánh giá mức độ phù hợp với vị trí tuyển dụng dưới đây.

=== VỊ TRÍ TUYỂN DỤNG ===
Tên vị trí     : {job.title}
Kinh nghiệm    : {exp_str}
Kỹ năng yêu cầu: {skill_str}
Mô tả công việc:
{(job.description or "")[:1500]}

=== THÔNG TIN BỔ SUNG VỀ ỨNG VIÊN ===
{extra_context.strip() if extra_context.strip() else "Không có thêm thông tin."}

=== YÊU CẦU ===
Chấm điểm mức độ phù hợp theo thang 0–100:
- 70–100 : Phù hợp cao
- 40–69  : Phù hợp trung bình
- 0–39   : Không phù hợp

Chỉ trả về một số nguyên duy nhất từ 0 đến 100. Không giải thích, không thêm ký tự khác."""

            # Tải ảnh từ Cloudinary về dạng bytes
            image_bytes = httpx.get(image_url, timeout=15).content

            client = _get_client()
            response = client.models.generate_content(
                model=_GEMINI_MODEL,
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                    prompt,
                ],
            )

            raw = response.text.strip()
            print(f"[MatchingService Vision] Gemini raw response: {raw!r}")

            numbers = re.findall(r"\b(\d{1,3})\b", raw)
            if numbers:
                score = int(numbers[0])
                return float(max(0, min(100, score)))

            print(f"[MatchingService Vision] Không parse được số từ response: {raw!r}")
            return None

        except Exception as e:
            print(f"[MatchingService Vision] Error: {e}")
            return None

    # ── Internal: Gemini text prompt (CV ONLINE / local file) ────
    @staticmethod
    def _call_gemini_text(
        job_title: str,
        job_description: str,
        job_skills: list[str],
        experience_required: int | None,
        cv_text: str,
    ) -> float | None:
        skill_str = ", ".join(job_skills) if job_skills else "Không có yêu cầu cụ thể"
        exp_str   = f"{experience_required}+ năm" if experience_required else "Không yêu cầu"

        prompt = f"""Bạn là chuyên gia tuyển dụng IT. Hãy đánh giá mức độ phù hợp của CV ứng viên với vị trí tuyển dụng dưới đây.

=== VỊ TRÍ TUYỂN DỤNG ===
Tên vị trí     : {job_title}
Kinh nghiệm    : {exp_str}
Kỹ năng yêu cầu: {skill_str}
Mô tả công việc:
{job_description[:1500]}

=== NỘI DUNG CV ỨNG VIÊN ===
{cv_text[:2500]}

=== YÊU CẦU ===
Chấm điểm mức độ phù hợp theo thang 0–100:
- 70–100 : Phù hợp cao
- 40–69  : Phù hợp trung bình
- 0–39   : Không phù hợp

Chỉ trả về một số nguyên duy nhất từ 0 đến 100. Không giải thích, không thêm ký tự khác."""

        try:
            client   = _get_client()
            response = client.models.generate_content(
                model=_GEMINI_MODEL,
                contents=prompt,
            )
            raw = response.text.strip()
            print(f"[MatchingService] Gemini raw response: {raw!r}")

            numbers = re.findall(r"\b(\d{1,3})\b", raw)
            if numbers:
                score = int(numbers[0])
                return float(max(0, min(100, score)))

            print(f"[MatchingService] Không parse được số từ response: {raw!r}")
            return None

        except Exception as e:
            print(f"[MatchingService] Gemini API error: {e}")
            return None
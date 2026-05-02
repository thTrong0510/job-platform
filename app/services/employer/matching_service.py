"""
Tính điểm phù hợp giữa CV ứng viên và Job Description bằng Gemini API.

Luồng:
  1. Kiểm tra DB (job_recommendations) — nếu đã có score thì dùng lại.
  2. Nếu chưa có → extract text CV → gọi Gemini → lưu DB.
  3. Force recalculate: xóa record cũ rồi tính lại.
"""
import os
import re
 
from app.extensions import db
from app.models.recommendation import JobRecommendation
from app.repositories.candidate.cv_skill_repository import CVSkillRepository
from app.repositories.candidate.skill_repository import SkillRepository
from app.services.employer.cv_text_extractor import CVTextExtractor
 
 
# ── Khởi tạo Gemini client (lazy singleton) ──────────────────────
_client = None
 
 
def _get_client():
    global _client
    if _client is None:
        from google import genai
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY chưa được cấu hình trong file .env"
            )
        _client = genai.Client(api_key=api_key)
    return _client
 
 
# Model gemini
_GEMINI_MODEL = "gemini-2.5-flash" 
 
 
# ─────────────────────────────────────────────────────────────────
class MatchingService:
 
    # ── Public: lấy score (cache → tính mới) ──────────────────────
    @staticmethod
    def get_or_calculate(application) -> float | None:
        """
        Trả về score (0–100) từ DB nếu đã tính.
        Nếu chưa có → gọi Gemini để tính rồi lưu DB.
        """
        cached = MatchingService._load_from_db(
            application.cv.candidate_id, application.job_id
        )
        if cached is not None:
            return cached
        return MatchingService._calculate_and_save(application)
 
    # ── Public: force recalculate ──────────────────────────────────
    @staticmethod
    def recalculate(application) -> float | None:
        """Xóa cache cũ và tính lại."""
        MatchingService._delete_from_db(
            application.cv.candidate_id, application.job_id
        )
        return MatchingService._calculate_and_save(application)
 
    # ── Internal: load từ DB ──────────────────────────────────────
    @staticmethod
    def _load_from_db(candidate_id: int, job_id: int) -> float | None:
        rec = JobRecommendation.query.filter_by(
            candidate_id=candidate_id,
            job_id=job_id,
        ).first()
        if rec and rec.score is not None:
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
 
    # ── Internal: tổng hợp text → gọi Gemini ─────────────────────
    @staticmethod
    def _score(application) -> float | None:
        job = application.job
        cv  = application.cv
 
        # 1. Extract text từ CV (online: JSON, upload: PDF/DOCX)
        cv_text = CVTextExtractor.extract(cv)
 
        # 2. Kỹ năng trong CV
        skill_ids      = CVSkillRepository.get_skill_ids_by_cv(cv.id)
        cv_skills      = SkillRepository.get_by_ids(skill_ids)
        cv_skill_names = [s.name for s in cv_skills]
        if cv_skill_names:
            cv_text += "\nKỹ năng trong CV: " + ", ".join(cv_skill_names)
 
        # 3. Kỹ năng hồ sơ ứng viên
        cand_skill_names = [cs.skill.name for cs in cv.candidate.skills]
        if cand_skill_names:
            cv_text += "\nKỹ năng ứng viên: " + ", ".join(cand_skill_names)
 
        # 4. Thông tin bổ sung từ hồ sơ ứng viên
        if cv.candidate.total_experience_years:
            cv_text += f"\nTổng kinh nghiệm: {cv.candidate.total_experience_years} năm"
        if cv.candidate.current_title:
            cv_text += f"\nVị trí hiện tại: {cv.candidate.current_title}"
        if cv.candidate.bio:
            cv_text += f"\nGiới thiệu: {cv.candidate.bio}"
 
        # 5. Không có text → không tính được
        if not cv_text.strip():
            print(f"[MatchingService] CV #{cv.id} không có text để phân tích")
            return None
 
        # 6. Skills yêu cầu của job
        job_skill_names = [js.skill.name for js in job.skills]
 
        # 7. Gọi Gemini
        return MatchingService._call_gemini(
            job_title=job.title,
            job_description=job.description or "",
            job_skills=job_skill_names,
            experience_required=job.experience_required,
            cv_text=cv_text,
        )
 
    # ── Internal: gọi Gemini API (google.genai mới) ───────────────
    @staticmethod
    def _call_gemini(
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
Chấm điểm mức độ phù hợp của CV với vị trí trên theo thang điểm 0–100:
- 70–100 : Phù hợp cao (kỹ năng và kinh nghiệm khớp tốt)
- 40–69  : Phù hợp trung bình (đáp ứng một phần yêu cầu)
- 0–39   : Không phù hợp (thiếu nhiều yêu cầu quan trọng)
 
Chỉ trả về một số nguyên duy nhất từ 0 đến 100. Không giải thích, không thêm ký tự khác."""
 
        try:
            client   = _get_client()
            response = client.models.generate_content(
                model=_GEMINI_MODEL,
                contents=prompt,
            )
            raw = response.text.strip()
            print(f"[MatchingService] Gemini raw response: {raw!r}")
 
            # Parse số đầu tiên trong response
            numbers = re.findall(r"\b(\d{1,3})\b", raw)
            if numbers:
                score = int(numbers[0])
                return float(max(0, min(100, score)))
 
            print(f"[MatchingService] Không parse được số từ response: {raw!r}")
            return None
 
        except Exception as e:
            print(f"[MatchingService] Gemini API error: {e}")
            return None
from app import db
from app.models.candidateExperience import CandidateExperience
import re

from app.models.candidate import Candidate


class CandidateExperienceRepository:

    @staticmethod
    def replace_all(candidate_id, form_data):

        # Xóa cũ
        candidate = Candidate.query.get(candidate_id)
        candidate.experiences.clear()

        pattern = re.compile(r"experiences\[(\d+)\]\[(\w+)\]")
        grouped = {}

        for key, value in form_data.items():
            match = pattern.match(key)
            if not match:
                continue

            index = int(match.group(1))
            field = match.group(2)

            if index not in grouped:
                grouped[index] = {}

            grouped[index][field] = value.strip() if isinstance(value, str) else value

        for index in sorted(grouped.keys()):
            exp = grouped[index]

            if exp.get("company"):
                new_exp = CandidateExperience(
                    candidate_id=candidate_id,
                    company=exp.get("company", ""),
                    position=exp.get("position", ""),
                    start_date=exp.get("start_date", ""),
                    end_date=exp.get("end_date", ""),
                    description=exp.get("description", "")
                )
                db.session.add(new_exp)

        db.session.commit()
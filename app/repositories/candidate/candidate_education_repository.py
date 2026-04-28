from app import db
from app.models.candidateEducation import CandidateEducation
import re

from app.models.candidate import Candidate


class CandidateEducationRepository:

    @staticmethod
    def replace_all(candidate_id, form_data):

        candidate = Candidate.query.get(candidate_id)
        candidate.educations.clear()

        pattern = re.compile(r"educations\[(\d+)\]\[(\w+)\]")
        grouped = {}

        for key, value in form_data.items():
            match = pattern.match(key)
            if not match:
                continue

            index = int(match.group(1))
            field = match.group(2)

            if index not in grouped:
                grouped[index] = {}

            grouped[index][field] = value

        for index in grouped:
            edu = grouped[index]

            if edu.get("school"):
                new_edu = CandidateEducation(
                    candidate_id=candidate_id,
                    school=edu.get("school", ""),
                    degree=edu.get("degree", ""),
                    start_date=edu.get("start_date", ""),
                    end_date=edu.get("end_date", "")
                )
                db.session.add(new_edu)

        db.session.commit()
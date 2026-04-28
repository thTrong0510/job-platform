from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models.candidate import Candidate
from app.models.skill import CandidateSkill


class CandidateRepository:

    @staticmethod
    def save(candidate):
        db.session.add(candidate)
        db.session.commit()
        return candidate

    @staticmethod
    def get_full_profile(candidate_id: int):
        return (
            Candidate.query
            .options(
                joinedload(Candidate.user),  # load email
                joinedload(Candidate.skills).joinedload(CandidateSkill.skill),
                joinedload(Candidate.experiences),
                joinedload(Candidate.educations)
            )
            .filter(Candidate.id == candidate_id)
            .first()
        )

    @staticmethod
    def get_full_by_id(candidate_id):
        return (
            Candidate.query
            .filter_by(id=candidate_id)
            .first()
        )

    @staticmethod
    def update_basic_info(candidate_id, form_data):
        candidate = Candidate.query.get(candidate_id)

        candidate.full_name = form_data.get("full_name", "")
        candidate.phone = form_data.get("phone", "")
        candidate.current_title = form_data.get("current_title", "")
        candidate.bio = form_data.get("bio", "")
        candidate.location = form_data.get("location", "")

        db.session.commit()

    @staticmethod
    def update_bio(candidate_id, form_data):
        candidate = Candidate.query.get(candidate_id)
        candidate.bio = form_data.get("bio", "")
        db.session.commit()
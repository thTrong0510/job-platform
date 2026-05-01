from app.extensions import db
from app.models.skill import CandidateSkill
from app.models.candidate import Candidate


class CandidateSkillRepository:

    @staticmethod
    def replace_all(candidate_id, form_data):

        candidate = Candidate.query.get(candidate_id)
        candidate.skills.clear()

        skill_ids = form_data.getlist("skills")

        for skill_id in skill_ids:
            if not skill_id:
                continue

            new_skill = CandidateSkill(
                candidate_id=candidate_id,
                skill_id=int(skill_id)
            )

            db.session.add(new_skill)

        db.session.commit()

    @staticmethod
    def replace_all_from_ids(candidate_id, skill_ids: list[int]):
        candidate = Candidate.query.get(candidate_id)
        candidate.skills.clear()
        for skill_id in skill_ids:
            db.session.add(CandidateSkill(
                candidate_id=candidate_id,
                skill_id=int(skill_id)
            ))
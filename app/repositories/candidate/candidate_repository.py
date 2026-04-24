from app.models.candidate import Candidate
from app.extensions import db

class CandidateRepository:

    @staticmethod
    def save(candidate):
        db.session.add(candidate)
        db.session.commit()
        return candidate
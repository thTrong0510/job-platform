from app.repositories.candidate.candidate_repository import CandidateRepository

class CandidateService:
    def save_candidate(candidate):
        return CandidateRepository.save(candidate)
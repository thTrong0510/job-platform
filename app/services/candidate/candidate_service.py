from app.repositories.candidate.candidate_repository import CandidateRepository
from app.repositories.candidate.candidate_education_repository import CandidateEducationRepository
from app.repositories.candidate.candidate_experience_repository import CandidateExperienceRepository
from app.repositories.candidate.candidate_skill_repository import CandidateSkillRepository


class CandidateService:
    def save_candidate(candidate):
        return CandidateRepository.save(candidate)

    @staticmethod
    def get_candidate_profile(candidate_id: int):
        candidate = CandidateRepository.get_full_profile(candidate_id)

        if not candidate:
            return None

        return candidate

    @staticmethod
    def update_profile(candidate_id, form_data):

        section = form_data.get("section")

        if section == "all":
            CandidateRepository.update_basic_info(candidate_id, form_data)
            CandidateRepository.update_bio(candidate_id, form_data)
            CandidateExperienceRepository.replace_all(candidate_id, form_data)
            CandidateEducationRepository.replace_all(candidate_id, form_data)
            CandidateSkillRepository.replace_all(candidate_id, form_data)

        elif section == "basic":
            CandidateRepository.update_basic_info(candidate_id, form_data)

        elif section == "bio":
            CandidateRepository.update_bio(candidate_id, form_data)

        elif section == "experiences":
            CandidateExperienceRepository.replace_all(candidate_id, form_data)

        elif section == "educations":
            CandidateEducationRepository.replace_all(candidate_id, form_data)

        elif section == "skills":
            CandidateSkillRepository.replace_all(candidate_id, form_data)

    @staticmethod
    def get_full_profile(candidate_id):
        return CandidateRepository.get_full_by_id(candidate_id)

    @staticmethod
    def get_candidate_by_id(candidate_id):
        return CandidateRepository.get_full_by_id(candidate_id)
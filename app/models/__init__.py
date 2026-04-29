# import all models to register metadata
from .user import User
from .candidate import Candidate
from .employer import Employer
from .skill import Skill, CandidateSkill, CVSkill, JobSkill
from .cv import CV, CVTemplate
from .job import Job
from .application import Application
from .recommendation import JobRecommendation
from .candidateEducation import CandidateEducation
from .candidateExperience import CandidateExperience
from .notification import Notification
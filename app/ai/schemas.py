from pydantic import BaseModel, Field
from typing import List, Optional


class ExperienceExtract(BaseModel):
    company: str
    position: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None


class EducationExtract(BaseModel):
    school: str
    degree: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class CVExtractForProfile(BaseModel):
    full_name: str
    phone: Optional[str] = None
    location: Optional[str] = None
    bio: Optional[str] = None
    current_title: Optional[str] = None
    experiences: List[ExperienceExtract] = Field(default_factory=list)
    educations: List[EducationExtract] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
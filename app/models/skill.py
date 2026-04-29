from app.extensions import db

class Skill(db.Model):
    __tablename__ = "skills"

    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)


# ===================================================
# CandidateSkill (composite PK)
# ===================================================

class CandidateSkill(db.Model):
    __tablename__ = "candidate_skills"

    candidate_id = db.Column(
        db.BigInteger,
        db.ForeignKey("candidates.id", ondelete="CASCADE"),
        primary_key=True
    )

    skill_id = db.Column(
        db.BigInteger,
        db.ForeignKey("skills.id", ondelete="RESTRICT"),
        primary_key=True
    )

    candidate = db.relationship("Candidate", back_populates="skills")
    skill = db.relationship("Skill")


# ===================================================
# CVSkill
# ===================================================

class CVSkill(db.Model):
    __tablename__ = "cv_skills"

    cv_id = db.Column(
        db.BigInteger,
        db.ForeignKey("cvs.id", ondelete="CASCADE"),
        primary_key=True
    )

    skill_id = db.Column(
        db.BigInteger,
        db.ForeignKey("skills.id", ondelete="RESTRICT"),
        primary_key=True
    )

    cv = db.relationship("CV", back_populates="skills")
    skill = db.relationship("Skill")


# ===================================================
# JobSkill
# ===================================================

class JobSkill(db.Model):
    __tablename__ = "job_skills"

    job_id = db.Column(
        db.BigInteger,
        db.ForeignKey("jobs.id", ondelete="CASCADE"),
        primary_key=True
    )

    skill_id = db.Column(
        db.BigInteger,
        db.ForeignKey("skills.id", ondelete="RESTRICT"),
        primary_key=True
    )

    job = db.relationship("Job", back_populates="skills")
    skill = db.relationship("Skill")
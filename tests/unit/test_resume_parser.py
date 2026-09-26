from pathlib import Path
from agent.resume_parser import (
    _clean_extracted_text,
    _create_fallback_profile,
    extract_json_from_llm,
)
from database.database import DatabaseManager
from database.repository import JobRepository
from models.schemas import (
    CategorizedSkills,
    EducationItem,
    ParsedResumeProfile,
    ProjectItem,
    ResumeRecord,
    WorkExperienceItem,
)


def test_clean_extracted_text():
    raw = "John   Doe \n\n\n\nSoftware   Engineer\n\n\nSkills"
    cleaned = _clean_extracted_text(raw)
    assert "   " not in cleaned
    assert "\n\n\n" not in cleaned
    assert "John Doe" in cleaned
    assert "Software Engineer" in cleaned


def test_extract_json_from_llm():
    # Markdown fence
    fence = '```json\n{"name": "Alice", "total_experience_years": 5.0}\n```'
    parsed = extract_json_from_llm(fence)
    assert parsed.get("name") == "Alice"
    assert parsed.get("total_experience_years") == 5.0

    # Raw braces
    raw = 'Here is the extracted JSON: {"name": "Bob", "skills": {"all_skills": ["Python"]}}'
    parsed2 = extract_json_from_llm(raw)
    assert parsed2.get("name") == "Bob"

    # Empty
    assert extract_json_from_llm("") == {}


def test_create_fallback_profile():
    text = "Jane Doe jane@example.com (555) 123-4567. Experience with Python, Docker, and AWS."
    profile = _create_fallback_profile(text)
    assert profile.email == "jane@example.com"
    assert "Python" in profile.skills.all_skills
    assert "Docker" in profile.skills.all_skills
    assert "AWS" in profile.skills.all_skills


def test_save_and_get_resume(tmp_path: Path):
    db_file = tmp_path / "test_resume.db"
    db = DatabaseManager(db_file)
    db.connect()
    db.run_migrations()
    repo = JobRepository(db)

    profile = ParsedResumeProfile(
        name="Alex Smith",
        headline="Staff Backend Engineer",
        email="alex@smith.io",
        total_experience_years=6.5,
        skills=CategorizedSkills(
            languages=["Python", "Go"],
            frameworks_and_libraries=["FastAPI"],
            databases=["PostgreSQL"],
            all_skills=["Python", "Go", "FastAPI", "PostgreSQL"],
        ),
        work_experience=[
            WorkExperienceItem(
                company="TechCorp",
                role="Senior Engineer",
                start_date="2020",
                end_date="Present",
                is_current=True,
                technologies=["Python", "FastAPI"],
                achievements=["Improved API throughput by 40%"],
            )
        ],
        projects=[
            ProjectItem(
                title="JobHunterAgent",
                technologies=["FastAPI", "React"],
                description="Autonomous job agent",
            )
        ],
        education=[
            EducationItem(
                institution="MIT",
                degree="B.S. CS",
                graduation_year="2018",
            )
        ],
    )

    record = ResumeRecord(
        id="resume-001",
        filename="alex_resume.pdf",
        file_path="/tmp/alex_resume.pdf",
        file_type="pdf",
        raw_text="Raw resume content here...",
        parsed_profile=profile,
        candidate_name=profile.name,
        headline=profile.headline,
        email=profile.email,
        total_yoe=profile.total_experience_years,
        is_active=True,
    )

    repo.save_resume(record)

    fetched = repo.get_resume("resume-001")
    assert fetched is not None
    assert fetched.candidate_name == "Alex Smith"
    assert fetched.total_yoe == 6.5
    assert fetched.is_active is True
    assert fetched.parsed_profile is not None
    assert "Python" in fetched.parsed_profile.skills.languages
    assert len(fetched.parsed_profile.work_experience) == 1
    assert fetched.parsed_profile.work_experience[0].company == "TechCorp"

    active = repo.get_active_resume()
    assert active is not None
    assert active.id == "resume-001"

    # Add second resume and set active
    record2 = ResumeRecord(
        id="resume-002",
        filename="alex_v2.pdf",
        file_path="/tmp/alex_v2.pdf",
        file_type="pdf",
        raw_text="V2 content",
        candidate_name="Alex Smith Jr",
        is_active=False,
    )
    repo.save_resume(record2)

    all_resumes = repo.list_resumes()
    assert len(all_resumes) == 2

    # Switch active
    repo.set_active_resume("resume-002")
    new_active = repo.get_active_resume()
    assert new_active is not None
    assert new_active.id == "resume-002"

    # Delete
    deleted_path = repo.delete_resume("resume-002")
    assert deleted_path == "/tmp/alex_v2.pdf"
    assert repo.get_resume("resume-002") is None
    # alex_resume should be active again
    assert repo.get_active_resume().id == "resume-001"

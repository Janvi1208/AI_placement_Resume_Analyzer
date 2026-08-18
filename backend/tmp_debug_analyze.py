from bson import ObjectId
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.auth.dependencies import get_current_user

user = {"_id": ObjectId(), "email": "a@b.com"}
resume_id = ObjectId()
jd_id = ObjectId()

class DummyUsers:
    def __init__(self):
        self.find_one_and_update = AsyncMock(return_value={"_id": user["_id"], "free_analyses_remaining": 1, "paid_credits": 0})
        self.update_one = AsyncMock(return_value=None)

class DummyResumes:
    def __init__(self):
        self.find_one = AsyncMock(return_value={
            "_id": resume_id,
            "user_id": user["_id"],
            "raw_text": "Python React Docker",
            "parsed": {
                "name": "A",
                "email": "a@b.com",
                "phone": None,
                "education": [],
                "skills": ["python", "react", "docker"],
                "experience": ["Worked on backend"],
                "projects": ["Project"],
                "certifications": [],
                "achievements": [],
            },
        })

class DummyJobs:
    def __init__(self):
        self.find_one = AsyncMock(return_value={
            "_id": jd_id,
            "user_id": user["_id"],
            "parsed": {
                "role": "Developer",
                "company": "X",
                "required_skills": ["python", "react"],
                "preferred_skills": ["docker"],
                "responsibilities": [],
                "experience_required": "2 years",
                "education_required": [],
                "tools": [],
                "technologies": [],
            },
        })

class DummyAnalyses:
    def __init__(self):
        self.insert_one = AsyncMock(return_value=type("R", (), {"inserted_id": ObjectId()})())

class DummyUsage:
    def __init__(self):
        self.insert_one = AsyncMock(return_value=None)

mock_db = {
    "users": DummyUsers(),
    "resumes": DummyResumes(),
    "job_descriptions": DummyJobs(),
    "analyses": DummyAnalyses(),
    "usage": DummyUsage(),
}

from app import routers as r
r.analyze.get_db = lambda: mock_db
app.dependency_overrides[get_current_user] = lambda: user

client = TestClient(app)
resp = client.post('/api/v1/analyze/readiness', json={
    'resume_id': str(resume_id),
    'job_description_id': str(jd_id),
})
print('STATUS', resp.status_code)
print(resp.text)

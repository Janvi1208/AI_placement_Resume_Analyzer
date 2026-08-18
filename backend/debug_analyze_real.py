from types import SimpleNamespace
from bson import ObjectId
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.auth.dependencies import get_current_user

user = {"_id": ObjectId(), "email": "a@b.com"}
resume_id = ObjectId()
jd_id = ObjectId()

resume_doc = {
    '_id': resume_id,
    'user_id': user['_id'],
    'raw_text': 'Python React Docker',
    'parsed': {
        'name': 'A',
        'email': 'a@b.com',
        'phone': None,
        'education': [],
        'skills': ['python', 'react', 'docker'],
        'experience': ['Worked on backend'],
        'projects': ['Project'],
        'certifications': [],
        'achievements': [],
    },
}

jd_doc = {
    '_id': jd_id,
    'user_id': user['_id'],
    'parsed': {
        'role': 'Developer',
        'company': 'X',
        'required_skills': ['python', 'react'],
        'preferred_skills': ['docker'],
        'responsibilities': [],
        'experience_required': '2 years',
        'education_required': [],
        'tools': [],
        'technologies': [],
    },
}

db = SimpleNamespace(
    resumes=SimpleNamespace(find_one=AsyncMock(return_value=resume_doc)),
    job_descriptions=SimpleNamespace(find_one=AsyncMock(return_value=jd_doc)),
    analyses=SimpleNamespace(insert_one=AsyncMock(return_value=SimpleNamespace(inserted_id=ObjectId()))),
    usage=SimpleNamespace(insert_one=AsyncMock(return_value=None)),
    users=SimpleNamespace(find_one_and_update=AsyncMock(return_value={"_id": user['_id'], "free_analyses_remaining": 1}), update_one=AsyncMock(return_value=None)),
)

def main():
    app.dependency_overrides[get_current_user] = lambda: user
    with patch('app.routers.analyze.get_db', return_value=db):
        client = TestClient(app)
        resp = client.post('/api/v1/analyze/readiness', json={'resume_id': str(resume_id), 'job_description_id': str(jd_id)})
        print('STATUS', resp.status_code)
        print(resp.text)
    app.dependency_overrides.clear()


if __name__ == '__main__':
    main()

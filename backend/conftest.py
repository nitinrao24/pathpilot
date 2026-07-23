import pytest
from models.db import init_db

@pytest.fixture(autouse=True, scope="session")
def setup_db():
    init_db()

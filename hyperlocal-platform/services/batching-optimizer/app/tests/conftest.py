import sys
import os
from pathlib import Path

# Add the project root to the python path
root_dir = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root_dir))

import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.main import app

# Create a mock session dependency for database
mock_db = MagicMock(spec=Session)

# Mock the query return values to prevent division by zero or DB errors
mock_query = MagicMock()
mock_query.order_by.return_value.limit.return_value.all.return_value = []
mock_query.all.return_value = []
mock_db.query.return_value = mock_query

def get_mock_db():
    try:
        yield mock_db
    finally:
        pass

app.dependency_overrides[get_db] = get_mock_db

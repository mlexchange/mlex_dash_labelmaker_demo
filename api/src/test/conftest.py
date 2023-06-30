from fastapi.testclient import TestClient
import pytest
import mongomock

from src.api import app, set_data_service
from src.data_service import DataService


@pytest.fixture(scope="module")
def mongodb():
    return mongomock.MongoClient().db


@pytest.fixture(scope="module")
def data_svc(mongodb):
    data_svc = DataService(mongodb)
    return data_svc


@pytest.fixture(scope="module")
def rest_client(data_svc):
    set_data_service(data_svc)
    return TestClient(app)
from fastapi.testclient import TestClient

from src.api import API_URL_PREFIX
from src.model import Dataset, DataPath


def test_datapath(rest_client: TestClient):
    init_response = rest_client.post(API_URL_PREFIX + "/dataset", json=dataset1)
    assert init_response.status_code == 200
    user_id = dataset1["user_id"]
    response = rest_client.get(API_URL_PREFIX + "/dataset", json={"user_id": user_id})
    print(response.json())
    dataset = Dataset.parse_obj(response.json())
    assert dataset.uid ==  init_response.json()
    response = rest_client.post(API_URL_PREFIX + "/dataset", json=dataset2)
    assert response.status_code == 200
    response = rest_client.get(API_URL_PREFIX + "/dataset", json={"user_id": user_id})
    mod_dataset = Dataset.parse_obj(response.json())
    assert mod_dataset.uid == dataset.uid
    pass



dataset1={
    "user_id": "test_user",
    "datapath": {
        "file_path": ["path/to/data"],
        "file_type": "dir",
        "file_location": "local"
    }
}


dataset2={
    "user_id": "test_user",
    "datapath": {
        "file_path": ["path/to/data"],
        "file_type": "dir",
        "file_location": "local"
    },
    "labelpath": {
        "file_path": ["path/to/label"],
        "file_type": "dir",
        "file_location": "local"
    }
}
import pytest
import asyncio
from fastapi.testclient import TestClient
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

from app.main import app

client = TestClient(app)

TEST_DATA_DIR = Path(__file__).parent / "data"


@pytest.fixture(scope="module")
def inference_id_holder():
    return {"inference_id": None}


@pytest.mark.asyncio
async def test_classify_single_image_and_get_status(inference_id_holder):
    # Step 1: Upload a single image and get the inference_id
    image_path = TEST_DATA_DIR / "rabbit.jpg"
    with open(image_path, "rb") as img_file:
        response = client.post(
            "/api/v1/images/classify",
            files={"image": ("rabbit.jpg", img_file, "image/jpeg")},
            data={"user_id": "test_user", "inference_engine": "tflite"},
        )
    assert response.status_code == 202
    response_json = response.json()
    assert response_json["status"]["msg"] == "processing"
    assert "inference_id" in response_json["data"]

    # Store the inference_id for later use
    inference_id_holder["inference_id"] = response_json["data"]["inference_id"]

    # Step 2: Wait for the inference to complete (simulate processing time)
    await asyncio.sleep(5)

    # Step 3: Get the status of the inference
    inference_id = inference_id_holder["inference_id"]
    response = client.get(f"/api/v1/images/classify/{inference_id}")
    assert response.status_code in [200, 202]
    response_json = response.json()
    assert "msg" in response_json["status"]
    assert response_json["status"]["msg"] in ["processing", "completed"]


@pytest.mark.asyncio
async def test_get_inference_status_processing(inference_id_holder):
    inference_id = inference_id_holder["inference_id"]
    response = client.get(f"/api/v1/images/classify/{inference_id}")
    assert response.status_code in [200, 202]
    assert "msg" in response.json()["status"]
    assert response.json()["status"]["msg"] in ["processing", "completed"]


@pytest.mark.asyncio
async def test_delete_inference_log_not_found():
    inference_id = "non_existing_inference_id"
    response = client.delete(f"/api/v1/logs/classify/{inference_id}")
    assert response.status_code == 404
    response_json = response.json()
    assert response_json["status"]["msg"] == "error"
    assert response_json["data"]["log"] == "no data"



@pytest.mark.asyncio
async def test_delete_inference_log(inference_id_holder):
    inference_id = inference_id_holder["inference_id"]
    response = client.delete(f"/api/v1/logs/classify/{inference_id}")

    assert response.status_code == 200
    response_json = response.json()
    assert response_json["status"]["msg"] == "success"
    assert response_json["data"]["log"] in ["already deleted", "deleted"]

@pytest.mark.asyncio
async def test_classify_images_from_zip_and_get_status():
    # Step 1: Upload a ZIP file containing images
    zip_file_path = TEST_DATA_DIR / "dataset.zip"
    with open(zip_file_path, "rb") as zip_file:
        response = client.post(
            "/api/v1/images/batch-classify",
            files={"zip_file": ("dataset.zip", zip_file, "application/zip")},
            data={"user_id": "test_user", "inference_engine": "tflite"},
        )
    assert response.status_code == 202
    response_json = response.json()
    assert response_json["status"]["msg"] == "processing"
    assert "inference_ids" in response_json["data"]

    # Extract one of the inference_ids for status check
    inference_ids = response_json["data"]["inference_ids"]
    assert len(inference_ids) > 0
    inference_id = inference_ids[0]

    # Step 2: Wait for the inference to complete (simulate processing time)
    await asyncio.sleep(5)

    # Step 3: Get the status of the inference
    response = client.get(f"/api/v1/images/classify/{inference_id}")
    assert response.status_code in [200, 202]
    response_json = response.json()
    assert "msg" in response_json["status"]
    assert response_json["status"]["msg"] in ["processing", "completed"]


@pytest.mark.asyncio
async def test_classify_single_image_invalid_inference_engine():
    image_path = TEST_DATA_DIR / "rabbit.jpg"
    with open(image_path, "rb") as img_file:
        response = client.post(
            "/api/v1/images/classify",
            files={"image": ("rabbit.jpg", img_file, "image/jpeg")},
            data={"user_id": "test_user", "inference_engine": "invalid_engine"},
        )
    assert response.status_code == 400
    response_json = response.json()
    assert response_json["status"]["msg"] == "not supported inference engine type"
    assert response_json["data"] == {}


@pytest.mark.asyncio
async def test_classify_images_from_zip_invalid_inference_engine():
    zip_file_path = TEST_DATA_DIR / "dataset.zip"
    with open(zip_file_path, "rb") as zip_file:
        response = client.post(
            "/api/v1/images/batch-classify",
            files={"zip_file": ("dataset.zip", zip_file, "application/zip")},
            data={"user_id": "test_user", "inference_engine": "invalid_engine"},
        )
    assert response.status_code == 400
    response_json = response.json()
    assert response_json["status"]["msg"] == "not supported inference engine type"
    assert response_json["data"] == {}


# ------------------------ LogRouter Tests ------------------------


@pytest.mark.asyncio
async def test_get_inference_log_success():
    request_data = {
        "user_id": "test_user",
        "start_time": "2024-01-01T00:00:00",
        "end_time": "2024-01-02T00:00:00",
        "min_runtime": 0.0,
        "max_runtime": 10.1,
        "page": 1,
        "offset": 10,
    }
    response = client.post("/api/v1/logs/classify", json=request_data)
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["status"]["msg"] == "success"
    assert "total_count" in response_json["data"]
    assert "log" in response_json["data"]


@pytest.mark.asyncio
async def test_get_inference_log_missing_user_id():
    request_data = {
        "start_time": "2024-01-01T00:00:00",
        "end_time": "2024-01-02T00:00:00",
        "min_runtime": 0,
        "max_runtime": 10,
        "page": 1,
        "offset": 10,
    }
    response = client.post("/api/v1/logs/classify", json=request_data)
    assert response.status_code == 422  # Missing required fields
    assert "detail" in response.json()


# ------------------------ Edge Cases and Exception Handling ------------------------


@pytest.mark.asyncio
async def test_classify_single_image_missing_user_id():
    image_path = TEST_DATA_DIR / "rabbit.jpg"
    with open(image_path, "rb") as img_file:
        response = client.post(
            "/api/v1/images/classify",
            files={"image": ("rabbit.jpg", img_file, "image/jpeg")},
            data={"inference_engine": "tflite"},  # Missing user_id
        )
    assert response.status_code == 422
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_classify_images_from_zip_invalid_file_type():
    invalid_file_path = TEST_DATA_DIR / "invalid.txt"
    with open(invalid_file_path, "rb") as invalid_file:
        response = client.post(
            "/api/v1/images/batch-classify",
            files={"zip_file": ("invalid.txt", invalid_file, "text/plain")},
            data={"user_id": "test_user", "inference_engine": "tflite"},
        )
    assert response.status_code == 500


@pytest.mark.asyncio
async def test_classify_images_from_empty_zip():
    empty_zip_path = TEST_DATA_DIR / "empty.zip"
    with open(empty_zip_path, "wb") as empty_zip:
        pass

    with open(empty_zip_path, "rb") as zip_file:
        response = client.post(
            "/api/v1/images/batch-classify",
            files={"zip_file": ("empty.zip", zip_file, "application/zip")},
            data={"user_id": "test_user", "inference_engine": "tflite"},
        )

    assert response.status_code == 500


import zipfile


@pytest.mark.asyncio
async def test_classify_images_from_zip_with_no_images():
    # Create a ZIP file with non-image files
    zip_with_no_images_path = TEST_DATA_DIR / "no_images.zip"
    with zipfile.ZipFile(zip_with_no_images_path, "w") as myzip:
        myzip.writestr("file.txt", "This is a text file")
        myzip.writestr("document.pdf", "This is a PDF file")

    with open(zip_with_no_images_path, "rb") as zip_file:
        response = client.post(
            "/api/v1/images/batch-classify",
            files={"zip_file": ("no_images.zip", zip_file, "application/zip")},
            data={"user_id": "test_user", "inference_engine": "tflite"},
        )

    assert response.status_code == 202
    response_json = response.json()
    assert response_json["status"]["msg"] == "processing"
    assert response_json["data"]["inference_ids"] == []


@pytest.mark.asyncio
async def test_classify_images_from_corrupted_zip():
    # Create a corrupted ZIP file for testing
    corrupted_zip_path = TEST_DATA_DIR / "corrupted.zip"
    with open(corrupted_zip_path, "wb") as corrupted_zip:
        corrupted_zip.write(b"This is not a valid ZIP file content")

    with open(corrupted_zip_path, "rb") as zip_file:
        response = client.post(
            "/api/v1/images/batch-classify",
            files={"zip_file": ("corrupted.zip", zip_file, "application/zip")},
            data={"user_id": "test_user", "inference_engine": "tflite"},
        )

    # Expecting a 500 error because the ZIP file is corrupted
    assert response.status_code == 500
    response_json = response.json()
    assert "msg" in response_json["status"]
    assert "File is not a zip file" in response_json["status"]["msg"]


"""
import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

from app.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert "welcome" in response.text


TEST_DATA_DIR = Path(__file__).parent / "data"


@pytest.mark.asyncio
async def test_classify_single_image():

    image_path = TEST_DATA_DIR / "rabbit.jpg"
    with open(image_path, "rb") as img_file:
        response = client.post(
            "/api/v1/images/classify",
            files={"image": ("rabbit.jpg", img_file, "image/jpeg")},
            data={"user_id": "test_user", "inference_engine": "tflite"},
        )

    assert response.status_code == 202
    assert response.json()["status"]["msg"] == "processing"
    assert "inference_id" in response.json()["data"]


@pytest.mark.asyncio
async def test_classify_images_from_zip():

    zip_file_path = TEST_DATA_DIR / "dataset.zip"
    with open(zip_file_path, "rb") as zip_file:
        response = client.post(
            "/api/v1/images/batch-classify",
            files={"zip_file": ("dataset.zip", zip_file, "application/zip")},
            data={"user_id": "test_user", "inference_engine": "tflite"},
        )

    assert response.status_code == 202
    assert response.json()["status"]["msg"] == "processing"
    assert "inference_ids" in response.json()["data"]


@pytest.mark.asyncio
async def test_get_inference_status_processing():

    inference_id = "SI-20240101010101-test_user"
    response = client.get(f"/api/v1/images/classify/{inference_id}")

    assert response.status_code in [200, 202]
    assert "msg" in response.json()["status"]
    assert response.json()["status"]["msg"] in ["processing", "completed", "no data"]


@pytest.mark.asyncio
async def test_get_inference_log():

    request_data = {
        "user_id": "test_user",
        "start_time": "2024-01-01T00:00:00",
        "end_time": "2024-01-02T00:00:00",
        "min_runtime": 0,
        "max_runtime": 10,
        "page": 1,
        "offset": 10,
    }

    response = client.post("/api/v1/logs/classify", json=request_data)

    assert response.status_code == 200
    response_json = response.json()
    assert response_json["status"]["msg"] == "success"
    assert "total_count" in response_json["data"]
    assert "log" in response_json["data"]


@pytest.mark.asyncio
async def test_delete_inference_log():

    inference_id = "test_inference_id"

    response = client.delete(f"/api/v1/logs/classify/{inference_id}")

    assert response.status_code in [200, 404]
    response_json = response.json()
    if response.status_code == 200:
        assert response_json["status"]["msg"] == "success"
        assert response_json["data"]["log"] in ["already deleted", "deleted"]
    elif response.status_code == 404:
        assert response_json["status"]["msg"] == "error"
        assert response_json["data"]["log"] == "no data"

"""

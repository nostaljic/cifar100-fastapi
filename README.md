# cifar100-fastapi-clean-architecture
cifar100 image classification backend with fastapi **clean architecture**

## Single-Image-File(JPG,PNG,JPEG ...) Classification
![SINGLE-ONNX](https://github.com/user-attachments/assets/f1c35d48-5c1a-4fa0-8f36-dbc1d0785219)

## Multiple-Files(ZIP) Classification
![BATCH-TFLITE](https://github.com/user-attachments/assets/555876e0-4a10-4c5c-bdfe-3f70707ff74e)



# Inference Server

This project is an image classification inference server based on FastAPI, utilizing ONNX and TFLite models to process image classification tasks. The server is containerized with Docker and integrates with Zenko-based S3 object storage, Redis, and a PostgreSQL database.
- **Development Device**: Macbook M3 Max
- **Development Environment**: Anaconda 24.9.2 + Python 3.11.10
* Developed using Python 3.11 (the `3.11-bullseye` version is recommended).
* Tested on macOS.


## Quick Start (Native)
### Prerequisites
- Docker and Docker Compose must be installed.
- The containers will be executed using the `docker-compose.yml` file in the root directory:
    - **Zenko Object Storage**: Runs an S3 object storage based on Zenko.
    - **Redis**: A Redis instance with a configured password.
    - **PostgreSQL**: Configures a PostgreSQL database.
- All data is stored as volumes under the `./docker` subdirectory, so the corresponding folders should be empty before use.
    - Example: `./docker/zenko/`, `./docker/postgresql/`, `./docker/redis/`
- Ensure that the environment settings are correctly configured using the provided `.env` file template.

### Environment Variables (.env Example)
```env
#Web Service
API_VERSION=1.0.0
APP_NAME=inference-server
DATABASE_DIALECT=postgresql
DATABASE_HOSTNAME=localhost
DATABASE_NAME=kpeppdb
DATABASE_PASSWORD=kpep1!
DATABASE_PORT=45432
DATABASE_USERNAME=kpep
DEBUG_MODE=true
S3_SCALITY_ACCESS_KEY_ID=kpep
S3_SCALITY_SECRET_ACCESS_KEY=kpep1!
S3_SCALITY_HOSTNAME=localhost
S3_SCALITY_PORT=48000
S3_SCALITY_BUCKET=bucketimg
REDIS_HOST=localhost
REDIS_PORT=46379
REDIS_DB=0
REDIS_PASSWORD=kpep1!
TFLITE_MODEL_PATH=/data/cifar100.tflite
ONNX_MODEL_PATH=/data/cifar100.onnx
CIFAR100_LABEL_PATH=/data/cifar100_label.json

# Docker
POSTGRES_USER=kpep
POSTGRES_PASSWORD=kpep1!
POSTGRES_DB=kpeppdb
MY_REDIS_PASSWORD=kpep1!
SCALITY_ACCESS_KEY_ID=kpep
SCALITY_SECRET_ACCESS_KEY=kpep1!
REMOTE_MANAGEMENT_DISABLE=1
```


## Setup Methods

### Method #1 (Anaconda)
1. Create a virtual environment using Anaconda:
   ```bash
   conda create -n kpep python=3.11
   ```

2. Verify the Python version:
   ```bash
   python --version  # Ensure it is 3.11.10
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements-noversion.txt  # Verify boto3, tensorflow, etc.
   ```

4. Start the containers:
   ```bash
   docker-compose up  # Ensure all 3 service containers are running
   ```

5. Run the Uvicorn server:
   ```bash
   uvicorn app.main:app
   ```


### Method #2 (Shell Script)
Run from the root directory of the Inference-Server project.

1. Ensure Python version 3.11.10 is available. If not, create a virtual environment using Anaconda.
2. Execute the `start.sh` script to set up dependencies and containers:
   ```bash
   sh ./start.sh
   ```

3. To stop the server, execute:
   ```bash
   sh ./stop.sh
   ```



#### Script Details
##### `start.sh`
```bash
#!/bin/bash
docker-compose up -d
python3.11 -m venv kpepai
source kpepai/bin/activate
pip install -r requirements-noversion.txt
python setup_bucket.py
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

##### `stop.sh`
```bash
#!/bin/bash
docker-compose down -v
rm -rf ./docker/postgresql/postgre_volume
rm -rf ./docker/redis/redis_volume
rm -rf ./docker/zenko/zenko_volume
echo "Stopping uvicorn server..."

PID=$(pgrep -f "app.main:app --host 0.0.0.0 --port 8000")
if [ -n "$PID" ]; then
    echo "Stopping uvicorn server with PID: $PID"
    kill -9 "$PID"
    echo "uvicorn server stopped."
else
    echo "No uvicorn server running."
fi

if [ -d "kpepai" ]; then
  rm -rf kpepai
  echo "[Deleted] venv kpepai"
else
  echo "[Not Found] venv kpepai"
fi
```

---

## Testing
A separate worker exists for background jobs. Testing requires the web server and all services (3 Docker containers) to be running.

### Test Method (Shell Script)
1. Prepare a Python environment that can execute `uvicorn app.main:app`.
2. Run the `test.sh` script:
   ```bash
   sh ./test.sh
   ```

3. Verify results
    ```bash
    =================================================================================== test session starts ===================================================================================
    platform darwin -- Python 3.11.10, pytest-8.3.3, pluggy-1.5.0
    rootdir: /Users/jaypyon/Documents/DEV/kpepai/Inference-Server
    plugins: asyncio-0.24.0, cov-6.0.0, anyio-3.6.2
    asyncio: mode=Mode.STRICT, default_loop_scope=None
    collected 16 items                                                                                                                                                                        

    tests/test_Inference.py ..............                                                                                                                                              [ 87%]
    tests/test_scheduler.py ..                                                                                                                                                          [100%]

    --------- coverage: platform darwin, python 3.11.10-final-0 ----------
    Name                                          Stmts   Miss  Cover   Missing
    ---------------------------------------------------------------------------
    app/routers/v1/ImageClassificationRouter.py      84     13    85%   95-97, 165, 175-176, 212-213, 226-232
    app/routers/v1/InferenceLogRouter.py             36     10    72%   35-37, 61-62, 69-70, 79-81
    app/routers/v1/SchedulerRouter.py                11      0   100%
    app/routers/v1/__init__.py                        0      0   100%
    ---------------------------------------------------------------------------
    TOTAL                                           131     23    82%


    =================================================================================== 16 passed in 14.27s ===================================================================================
    Wrote HTML report to htmlcov/index.html
    [Stopped] Uvicorn ASGI
    [+] Running 4/3
    ✔ Container postgres_db          Removed                                                                                                                                             0.2s 
    ✔ Container zenko_s3             Removed                                                                                                                                             0.2s 
    ✔ Container redis                Removed                                                                                                                                             0.2s 
    ✔ Network inference-server_kpep  Removed                                                                                                                                             0.0s 
    [Not Found] venv kpepai
    [Stopped] all processes
    test.sh: line 12: 38808 Killed: 9               nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 >> uvicorn.log 2>&1
    ```

##### `test.sh` Script Details
```bash
docker-compose up -d
echo "[START] Uvicorn Server..."
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 >> test.log 2>&1 & echo $! > test_uvicorn.pid
sleep 10
echo "[SETUP] Create Bucket..."
sleep 10
python setup_bucket.py
sleep 10
echo "[SETUP] Initial Settings..."
pytest --cov-report term-missing --cov=app/routers/v1
coverage html

if [ -f test_uvicorn.pid ]; then
  PID=$(cat test_uvicorn.pid)
  kill -9 $PID
  rm test_uvicorn.pid
else
  echo "[Not Found] PID"
fi
docker-compose down -v
rm -rf ./docker/postgresql/postgre_volume
rm -rf ./docker/redis/redis_volume
rm -rf ./docker/zenko/zenko_volume
```

---

## Models Used
- **ONNX**
- **TFLITE**

---

## API Documentation
Swagger Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

| **NO** | **Description**                                    | **Request Type** | **Endpoint**                                      | **Request URL Example**                                       | **Request BODY Example**                                    | **Response Example**                                       |
|----------|----------------------------------------------|---------------|-----------------------------------------------------|--------------------------------------------------------|------------------------------------------------------|-----------------------------------------------------|
| 1        | Single Image Classification (Form Data)           | `POST`        | `/api/v1/images/classify`                               | `http://127.0.0.1:8000/api/v1/images/classify`             | ```image=@"/path/to/image.jpg", user_id="user0", inference_engine="onnx"``` | ```{ "status": { "msg": "processing" }, "data": { "inference_id": "SI-20241112211549671062-user0" } }``` |
| 2        | Batch Image(ZIP) Classification (Form Data) | `POST`        | `/api/v1/images/batch-classify`                         | `http://127.0.0.1:8000/api/v1/images/batch-classify`       | ```zip_file=@"/path/to/image.zip", user_id="user_1", inference_engine="tflite"``` | ```{ "status": { "msg": "processing" }, "data": { "inference_ids": ["BI-20241112211549671062-user1-0", "BI-20241112211549671062-user1-1"] } }``` |
| 3        | Check Image Classification Status (Query Param)            | `GET`         | `/api/v1/images/classify/{inference_id}`                | `http://127.0.0.1:8000/api/v1/images/classify/SI-20241112211549671062-user0` | (empty)                                        | ```{ "status": { "msg": "processing" }, "data": { "inference_id": "SI-20241112211549671062-user0", "details": {...} } }``` or ```{ "status": { "msg": "completed" }, "data": { "inference_id": "SI-20241112211549671062-user0", "result": {...} } }``` |
| 4        | Check Image Classification Logs (JSON Body)              | `POST`        | `/api/v1/logs/classify`                                 | `http://127.0.0.1:8000/api/v1/logs/classify`               | ```{ "user_id": "user_1", "start_time": "2024-11-01T00:00:00Z", "end_time": "2024-11-10T23:59:59Z", "min_runtime": 0.02, "max_runtime": 0.1, "page": 1, "offset": 3 }``` | ```{ "status": { "msg": "success" }, "data": { "total_count": 10, "log": [...] } }``` |
| 5        | Delete Image Classification Logs (Query Param)            | `DELETE`      | `/api/v1/logs/classify/{inference_id}`                  | `http://127.0.0.1:8000/api/v1/logs/classify/SI-20241112223547698684-test_user` | (empty)                                        | ```{ "status": { "msg": "success" }, "data": { "log": "deleted" } }``` or ```{ "status": { "msg": "error" }, "data": { "log": "no data" } }``` |
| 6        | Update Clearing-up batch program deletion interval for Image Classification Logs (Query Param)          | `PUT`         | `/api/v1/schedule/interval`                             | `http://127.0.0.1:8000/api/v1/schedule/interval?interval=1` | (empty)                                        | ```{ "status": { "msg": "Cleanup interval updated to 1 minutes" } }``` |
| 7        | Update Clearing-up batch program deletion period for Image Classification Logs (Query Param)          | `PUT`         | `/api/v1/schedule/period`                               | `http://127.0.0.1:8000/api/v1/schedule/period?period=1`    | (empty)                                        | ```{ "status": { "msg": "Cleanup period updated to 1 days" } }``` |

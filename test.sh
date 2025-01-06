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
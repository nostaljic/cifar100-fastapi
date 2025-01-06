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

FROM mikesatmit/python311:latest
RUN apt-get update && apt-get install -y \
    gcc \
    libgl1-mesa-glx \
    libglib2.0-0
WORKDIR /app
COPY requirements-noversion.txt .
RUN pip install -r requirements-noversion.txt
COPY . .
CMD ["sh", "-c", "python setup_bucket.py && uvicorn app.main:app --host 0.0.0.0 --port 58000"]

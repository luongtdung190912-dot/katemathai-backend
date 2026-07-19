FROM python:3.10-slim
RUN apt-get update && apt-get install -y ffmpeg libcairo2-dev libpango1.0-dev freeglut3-dev pkg-config gcc && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8000
CMD ["uvicorn", "main.py:app", "--host", "0.0.0.0", "--port", "8000"]

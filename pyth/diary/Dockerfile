FROM python:3.12-slim

WORKDIR /service

RUN groupadd -g 1000 uvicorn && \
    useradd -u 1000 -g uvicorn -s /bin/sh -m uvicorn

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY diary ./diary
RUN chown -R uvicorn:uvicorn /service

USER uvicorn

CMD ["uvicorn", "diary.main:app", "--host", "0.0.0.0", "--port", "8000"]

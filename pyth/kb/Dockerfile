FROM tether-diary:latest

USER root
COPY kb ./kb
RUN chown -R uvicorn:uvicorn /service

USER uvicorn

CMD ["uvicorn", "kb.main:app", "--host", "0.0.0.0", "--port", "8000"]

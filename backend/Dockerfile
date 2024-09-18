FROM python:3.8-slim AS builder

WORKDIR /app

COPY pyproject.toml requirements.txt ./
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /wheels -r requirements.txt

COPY main.py init.py ./
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /wheels .

FROM python:3.8-slim AS runner
COPY --from=builder /wheels /wheels
RUN pip install --no-cache /wheels/* && rm -rf /wheels

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

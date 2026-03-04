FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
COPY src/ src/
COPY data/ data/
COPY cs_frontend/ cs_frontend/

RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["uvicorn", "src.contract_simulator.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

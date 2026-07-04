FROM python:3.11-slim

WORKDIR /app

RUN pip install uv

COPY pyproject.toml uv.lock ./

RUN uv pip install --system .

COPY . .

CMD ["uvicorn","app.main:app","--host","0.0.0.0","--reload"]
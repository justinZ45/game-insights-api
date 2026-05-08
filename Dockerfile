FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /usr/local/app

COPY pyproject.toml .

RUN pip install --no-cache-dir .

COPY src ./src

RUN useradd app && chown -R app /usr/local/app
USER app

EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
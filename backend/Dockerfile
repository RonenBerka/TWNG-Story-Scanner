FROM python:3.11-slim

WORKDIR /app

# Install dependencies first for layer caching
COPY pyproject.toml ./
RUN pip install --no-cache-dir \
    "fastapi>=0.115,<1" \
    "uvicorn[standard]>=0.30,<1" \
    "sqlalchemy>=2.0,<3" \
    "psycopg2-binary>=2.9,<3" \
    "alembic>=1.13,<2" \
    "pytest>=8,<9" \
    "httpx>=0.27,<1" \
    "python-jose[cryptography]>=3.3,<4" \
    "passlib[bcrypt]>=1.7,<2" \
    "bcrypt>=4.0,<5" \
    "praw>=7.7,<8" \
    "requests>=2.31,<3" \
    "celery[redis]>=5.3,<6" \
    "openai>=1.10,<2"

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

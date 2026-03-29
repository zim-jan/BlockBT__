FROM python:3.12-slim

# Install system dependencies required for building and running vectorbt
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen

# Copy the rest of the application code
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Run the application
CMD ["uv", "run", "uvicorn", "blockbt.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

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

# Expose Streamlit port
EXPOSE 8501

# Default to empty STREAMLIT_SERVER_ADDRESS if not provided to avoid conflicts
# It can be overriden in docker-compose.yml

# Run the application
CMD ["uv", "run", "streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]

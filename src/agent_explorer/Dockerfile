FROM python:3.13-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml uv.lock ./
COPY src/common ./src/common
COPY src/agent_explorer ./src/agent_explorer

# Install dependencies
RUN uv sync --frozen

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONPATH=/app

# Run the application
CMD ["uv", "run", "uvicorn", "src.agent_explorer.main:app", "--host", "0.0.0.0", "--port", "8000"]

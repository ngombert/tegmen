FROM python:3.13-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml uv.lock ./
COPY src/common ./src/common
COPY src/agent_maestro ./src/agent_maestro

# Install dependencies
RUN uv sync --frozen

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONPATH=/app
ENV MICROSERVICES_MODE=true

# Run the application
CMD ["uv", "run", "uvicorn", "src.agent_maestro.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Dockerfile for AskHR Agent - AgentCore Runtime
FROM public.ecr.aws/docker/library/python:3.10-slim

WORKDIR /app

# Copy requirements
COPY pyproject.toml ./

# Install dependencies
RUN pip install --no-cache-dir -e .

# Copy source code
COPY src/ ./src/

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose port for AgentCore
EXPOSE 8080

# Run the agent using the main.py entrypoint
CMD ["python", "src/main.py"]

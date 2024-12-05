# Base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install Python dependencies
RUN pip install --no-cache-dir transformers torch fastapi uvicorn

# Copy application files
COPY llm.py .

# Expose the port FastAPI will use
EXPOSE 5001

# Run the application
CMD ["uvicorn", "llm:app", "--host", "0.0.0.0", "--port", "5000"]

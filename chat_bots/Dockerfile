# Base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy chatbot script
COPY WHchatbot.py .

# Volume for shared `.smv` files
VOLUME /app/smv_files

# Default command
CMD ["python", "WHchatbot.py"]
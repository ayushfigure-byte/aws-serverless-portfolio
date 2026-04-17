FROM python:3.12-slim

# Install system dependencies for Chromium and Postgres
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for Selenium
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run the app
CMD ["python", "app.py"]

# Use a base image with Python
FROM python:3.11-slim

# Install Chrome and ChromeDriver dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip && \
    apt-get clean

# Install Google Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && apt-get install -y google-chrome-stable

# Install ChromeDriver
RUN wget -O /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/ && \
    rm /tmp/chromedriver.zip

# Set environment variables for Chrome and ChromeDriver
ENV CHROME_BIN=/usr/bin/google-chrome
ENV CHROME_DRIVER=/usr/local/bin/chromedriver
ENV PYTHONUNBUFFERED=1

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# ✅ Add this line to download the spaCy model
RUN python -m spacy download en_core_web_sm

# ✅ Download NLTK stopwords
RUN python -m nltk.downloader stopwords

# Copy application files and set working directory
COPY . /app
WORKDIR /app

# Expose port and run the application
EXPOSE 5000
CMD ["python", "app.py"]

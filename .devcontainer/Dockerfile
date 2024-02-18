FROM nikolaik/python-nodejs:python3.12-nodejs21-bullseye

# Install dependencies
RUN apt-get update && \
    apt-get install -y wget unzip xvfb libxcomposite1 libxcursor1 libxdamage1 libxi6 libxtst6 libnss3 libcups2 libxss1 libxrandr2 libasound2 libpangocairo-1.0-0 libatk1.0-0 libatk-bridge2.0-0 libgtk-3-0 libgbm1 && \
    rm -rf /var/lib/apt/lists/*

# Install AWS CLI
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \
    unzip awscliv2.zip && \
    ./aws/install && \
    rm -rf awscliv2.zip aws

# Add HashiCorp's official GPG key
RUN wget -qO- https://apt.releases.hashicorp.com/gpg | gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg

# Add HashiCorp's official repository
RUN echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com bullseye main" > /etc/apt/sources.list.d/hashicorp.list

# Install Terraform
RUN apt-get update && \
    apt-get install -yqq terraform && \
    rm -rf /var/lib/apt/lists/*

# Install Chrome and Chromedriver
RUN curl -Lo "/tmp/chromedriver.zip" "https://chromedriver.storage.googleapis.com/98.0.4758.48/chromedriver_linux64.zip" && \
    curl -Lo "/tmp/chrome-linux.zip" "https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F950363%2Fchrome-linux.zip?alt=media" && \
    unzip /tmp/chromedriver.zip -d /opt/ && \
    unzip /tmp/chrome-linux.zip -d /opt/ && \
    chmod +x /opt/chromedriver && \
    rm /tmp/chromedriver.zip /tmp/chrome-linux.zip

# Add Chromedriver to PATH
ENV PATH="/opt/chromedriver:${PATH}"

# Install Python package manager (Poetry)
RUN pip install poetry

# Copy Python project files
COPY calender/pyproject.toml .
COPY calender/poetry.loc[k] .

# Install Python dependencies
RUN poetry config virtualenvs.create false && poetry install --no-interaction
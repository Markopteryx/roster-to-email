FROM public.ecr.aws/lambda/python:3.9

RUN yum install -y wget unzip xorg-x11-server-Xvfb libXcomposite libXcursor libXdamage libXi libXtst nss cups-libs libXScrnSaver libXrandr alsa-lib pango atk at-spi2-atk gtk3 && \
    yum clean all

RUN curl -Lo "/tmp/chromedriver.zip" "https://chromedriver.storage.googleapis.com/98.0.4758.48/chromedriver_linux64.zip" && \
    curl -Lo "/tmp/chrome-linux.zip" "https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F950363%2Fchrome-linux.zip?alt=media" && \
    unzip /tmp/chromedriver.zip -d /opt/ && \
    unzip /tmp/chrome-linux.zip -d /opt/ && \
    chmod +x /opt/chromedriver && \
    rm /tmp/chromedriver.zip /tmp/chrome-linux.zip

ENV PATH="/opt/chromedriver:${PATH}"

RUN pip install poetry

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false && poetry install --no-interaction

COPY . .

CMD ["main.handler"]
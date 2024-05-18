ARG PYTHON=3.12

FROM python:${PYTHON}-slim

ADD https://repo1.maven.org/maven2/io/mfj/textricator/10.0.67/textricator-10.0.67-bin.tgz /tmp/textricator.tgz
RUN tar -xvf /tmp/textricator.tgz -C /opt
RUN ln -s /opt/textricator*/textricator /usr/local/bin/textricator

ADD https://github.com/pdf2htmlEX/pdf2htmlEX/releases/download/v0.18.8.rc1/pdf2htmlEX-0.18.8.rc1-master-20200630-Ubuntu-bionic-x86_64.deb /tmp/pdf2html.deb
ADD http://archive.ubuntu.com/ubuntu/pool/main/libj/libjpeg-turbo/libjpeg-turbo8_2.1.5-2ubuntu2_amd64.deb /tmp/libjpeg-turbo8.deb

RUN apt update
RUN apt install -y git openjdk-17-jre-headless python3-opencv /tmp/*.deb

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install 'poetry==1.8.*'
RUN poetry config virtualenvs.create false
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root

COPY . /app

# RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
# USER appuser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["python", "app.py"]

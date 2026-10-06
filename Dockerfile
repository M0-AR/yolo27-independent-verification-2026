FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl wget unzip libgl1 libglib2.0-0 libsm6 libxext6 libxrender1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /work

COPY requirements.txt /work/requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . /work

# Default: show help + run smoke (tiny, CPU, no weights fabrication)
CMD ["bash", "-c", "python -m src.verify_claims --help; python -m src.smoke_live"]

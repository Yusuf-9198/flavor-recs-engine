FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

WORKDIR /app

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

RUN python -c "import nltk; nltk.download('stopwords', quiet=True)"

EXPOSE 8000

CMD ["gunicorn", "--config", "gunicorn.conf.py", "wsgi:app"]

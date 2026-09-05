# Anxin backend with the Tesseract OCR engine baked in.
#
# Render's native `env: python` runtime has no Tesseract and no apt, so the
# Screenshot tab can never work there: pytesseract raises
# TesseractNotFoundError and /api/ocr returns "no text found" for every image.
# This image is the fix. To use it on Render, change the backend service in
# render.yaml to `env: docker` (see README, "Live deployment").
#
# Local use:
#   docker build -t anxin-backend backend
#   docker run --rm -p 8000:8000 --env-file backend/.env anxin-backend

FROM python:3.12-slim

# tesseract-ocr        the engine
# tesseract-ocr-chi-sim Simplified Chinese pack -- the app tries eng+chi_sim first
RUN apt-get update \
 && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-chi-sim \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Render injects $PORT; default to 8000 for local runs.
ENV PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]

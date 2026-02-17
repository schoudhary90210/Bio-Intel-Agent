FROM python:3.10-slim

WORKDIR /app

# Install gcc and build essentials to compile Biopython
RUN apt-get update && apt-get install -y gcc build-essential python3-dev

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

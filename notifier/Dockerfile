# Verwenden Sie ein Python-Image als Basis
FROM python:3.11-slim

# Arbeitsverzeichnis festlegen
WORKDIR /app

# Abhängigkeiten kopieren und installieren
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Anwendungscode kopieren
COPY . .

# Startbefehl festlegen
CMD ["python", "notifier.py"]

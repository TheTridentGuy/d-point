FROM python:slim
WORKDIR /
COPY . .
RUN pip3 install --no-cache-dir -r requirements.txt
RUN pip3 install --no-cache-dir gunicorn
RUN apt-get update && apt-get install -y --no-install-recommends \
    libatomic1 \
    && rm -rf /var/lib/apt/lists/*
RUN prisma generate
EXPOSE 5000
CMD ["gunicorn", "-w", "10", "-b", "0.0.0.0:5000", "server:app"]
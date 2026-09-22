FROM python:3.13-slim
WORKDIR /
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
RUN pip3 install --no-cache-dir gunicorn
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "10", "-b", "127.0.0.1:5000", "server:app"]
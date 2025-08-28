FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app /9_three_quarte/app
COPY logging.conf /app/logging.conf

COPY init.sh /a9_three_quarte/init.sh
RUN chmod +x /9_three_quarte/init.sh

EXPOSE 9943

# 啟動
ENTRYPOINT ["/bin/bash", "init.sh"]
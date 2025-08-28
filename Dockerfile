FROM python:3.10-slim

WORKDIR /9_three_quarter

# 安裝基本工具
RUN apt-get update && apt-get install -y --no-install-recommends \
    apt-utils \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 建立虛擬環境
RUN python -m venv /9_three_quarter/.venv
ENV VIRTUAL_ENV=/9_three_quarter/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH" 

# 複製 requirements 並安裝
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ARG TOKEN
ENV TOKEN=$TOKEN

COPY app /9_three_quarter/app
COPY logging.conf /9_three_quarter/logging.conf

COPY init.sh /9_three_quarter/init.sh
RUN chmod +x /9_three_quarter/init.sh

EXPOSE 9943

# 啟動
ENTRYPOINT ["/bin/bash", "init.sh"]



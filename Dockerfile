# 1. 使用官方的 Python 3.11 slim 作為基礎映像
FROM python:3.11-slim

# 2. 在容器內設定工作目錄
WORKDIR /app

# 3. 將專案所有檔案複製到容器的工作目錄中
#    注意：請確保您的 .env 檔案和金鑰檔案 (如 google-credentials.json) 不要直接複製到映像中，
#    這些敏感資訊應該在啟動容器時以環境變數的方式傳入。
COPY . .

# 4. 安裝 requirements.txt 中定義的 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 5. 讓 start.sh 可以被執行
RUN chmod +x start.sh

# 6. 開放容器的 $PORT 連接埠，以便外部可以存取 API 服務
ARG PORT=8080
EXPOSE $PORT

# 7. 設定啟動指令為 start.sh
CMD ["./start.sh"]

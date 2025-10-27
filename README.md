# 產業週報專案

本專案是一個使用 Python、React 和 Google Cloud 服務建立的全端 Web 應用程式，旨在提供產業週報和相關財務數據。

## 專案概述

- **後端**: 一個 Python 應用程式，定期從 FMP (Financial Modeling Prep) 獲取財務數據，使用生成式 AI (Google Generative AI 和 OpenAI) 產生報告，並將其儲存到 Firestore。它還提供一個 FastAPI 伺服器，以 API 端點的形式提供這些數據。
- **前端**: 一個 React 應用程式，使用後端提供的 API 來顯示產業數據和報告。

## 專案結構

```
industry_weekly/
├── .venv/                  # Python 虛擬環境
├── frontend/               # React 前端應用程式
│   ├── build/              # 前端應用程式的生產版本
│   ├── node_modules/       # Node.js 模組
│   ├── public/             # 公共資源
│   ├── src/                # React 應用程式的原始碼
│   ├── .gitignore
│   ├── package.json
│   ├── package-lock.json
│   └── tsconfig.json
├── output/                 # 輸出的報告 (如果適用)
├── prompts/                # Prompt 模板
├── __pycache__/            # Python 快取
├── .env                    # 環境變數檔案
├── .gitignore
├── .python-version
├── api_server.py           # FastAPI 伺服器
├── firestore_service.py    # Firestore 相關服務
├── fmp_client.py           # FMP API 客戶端
├── main.py                 # 主要應用程式進入點
├── pyproject.toml
├── README.md
├── report_generator.py     # 報告生成器
├── requirements.txt        # Python 依賴項
└── sp500_sector.py         # S&P 500 相關邏輯
```

## 開始使用

### 先決條件

- Python 3.9+
- Node.js 14+
- Google Cloud 帳戶和已設定的專案
- FMP API 金鑰
- Google Generative AI API 金鑰
- OpenAI API 金鑰

### 後端設定

1.  **安裝依賴項**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **設定環境變數**:
    複製 `.env.example` (如果有的話) 為 `.env` 並填寫以下變數：
    ```
    FMP_API_KEY=YOUR_FMP_API_KEY
    GENAI_API_KEY=YOUR_GENAI_API_KEY
    OPEN_AI_API=YOUR_OPEN_AI_API_KEY
    GOOGLE_APPLICATION_CREDENTIALS=path/to/your/google-credentials.json
    ```

### 前端設定

1.  **進入前端目錄**:
    ```bash
    cd frontend
    ```

2.  **安裝依賴項**:
    ```bash
    npm install
    ```

## 執行應用程式

### 後端

您可以直接執行 `main.py` 或 `sp500_sector.py` 來手動觸發任務。

- **生成報告**:
  ```bash
  python main.py
  ```

- **更新 S&P 500 數據**:
  ```bash
  python sp500_sector.py
  ```

### 排程執行

可以使用 `scheduler.py` 來排程執行後端任務。

- **執行排程器**:
  ```bash
  python scheduler.py
  ```

### 前端

1.  **執行後端 API 伺服器**:
    ```bash
    uvicorn api_server:app --reload
    ```

2.  **執行前端應用程式**:
    在另一個終端中，進入 `frontend` 目錄並執行：
    ```bash
    npm start
    ```

## API 端點

- `GET /api/industry-data`: 獲取所有產業的數據。
- `GET /api/industry-reports/{industry_name}/latest`: 獲取指定產業的最新報告。
- `GET /api/industry-reports/{industry_name}/{report_date}`: 獲取指定產業和日期的特定報告。

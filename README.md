# Google Maps 餐廳評論 AI 分析機器人

這是一個 Line Bot，可以接收使用者分享的 Google Maps 餐廳連結，自動抓取評論並使用 AI 進行分析。

## 功能特色

- 🕵️ **洗評偵測**：識別「打卡送肉」、「五星好評送小菜」等洗評行為
- 🥘 **菜色推薦**：從真實評論中挖掘最受歡迎的必點菜色
- ⭐️ **真實評分**：排除洗評後的校正評分
- 📱 **美觀介面**：使用 Line Flex Message 呈現分析結果

## 安裝教學

1. 安裝依賴套件：
   ```bash
   pip install -r requirements.txt
   playwright install
   ```

2. 設定環境變數：
   複製 `.env.example` 為 `.env` 並填入您的 API Key：
   - LINE Channel Secret & Access Token
   - Gemini API Key

3. 啟動伺服器：
   ```bash
   python app.py
   ```

## 技術架構

- Backend: Flask
- AI: Google Gemini Pro
- Scraping: Playwright / SerpApi
- Platform: LINE Messaging API

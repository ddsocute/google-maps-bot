import os
import sys

# Add the parent directory to sys.path so we can import modules from the root
# This is critical for Vercel to find 'modules' when running api/index.py
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FlexSendMessage
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Line Bot Configuration
CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')

# Vercel might not have .env loaded in the same way, but it injects env vars.
# We skip the sys.exit check to avoid crashing the build if vars are missing during build time.
if not CHANNEL_ACCESS_TOKEN or not CHANNEL_SECRET:
    print('Warning: LINE_CHANNEL_ACCESS_TOKEN and LINE_CHANNEL_SECRET are missing.')

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN) if CHANNEL_ACCESS_TOKEN else None
handler = WebhookHandler(CHANNEL_SECRET) if CHANNEL_SECRET else None

@app.route("/callback", methods=['POST'])
def callback():
    if not handler:
        abort(500)
        
    # get X-Line-Signature header value
    signature = request.headers.get('X-Line-Signature')

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

@app.route("/health", methods=['GET'])
def health():
    return 'OK', 200

# Only add handler if it exists
if handler:
    @handler.add(MessageEvent, message=TextMessage)
    def handle_message(event):
        msg_text = event.message.text
        
        # Check if it contains a Google Maps link
        if "maps.app.goo.gl" in msg_text or "google.com/maps" in msg_text:
            try:
                # 0. Notify user processing started
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="🔍 收到連結！食探 AI 正在前往現場偵查... (約需 10-15 秒)")
                )
                
                # 1. Parse URL
                from modules.url_parser import GoogleMapsURLParser
                target_url = GoogleMapsURLParser.get_clean_url(msg_text)
                
                if not target_url:
                    line_bot_api.push_message(
                        event.source.user_id,
                        TextSendMessage(text="❌ 無法解析此連結，請確認是有效的 Google Maps 連結。")
                    )
                    return

                # 2. Scrape Data
                from modules.scraper import GoogleMapsScraper
                scraper = GoogleMapsScraper(headless=True)
                reviews = scraper.scrape_reviews(target_url, max_reviews=25)
                
                if not reviews:
                    line_bot_api.push_message(
                        event.source.user_id,
                        TextSendMessage(text="❌ 抓取評論失敗，可能是網路問題或 Google 擋住了請求。請稍後再試。")
                    )
                    return

                # 3. Analyze with AI
                from modules.ai_analyzer import AIAnalyzer
                analyzer = AIAnalyzer()
                # Try to get restaurant name from first review or URL (simplified)
                restaurant_name = "餐廳" 
                
                analysis_result = analyzer.analyze_reviews(reviews, restaurant_name=restaurant_name)
                
                if "error" in analysis_result:
                    line_bot_api.push_message(
                        event.source.user_id,
                        TextSendMessage(text=f"❌ AI 分析失敗: {analysis_result['error']}")
                    )
                    return

                # 4. Reply with Flex Message
                from modules.line_messenger import LineMessenger
                flex_message = LineMessenger.create_analysis_flex_message(analysis_result, restaurant_name, target_url)
                
                line_bot_api.push_message(
                    event.source.user_id,
                    flex_message
                )
                
            except Exception as e:
                print(f"Error processing message: {e}")
                line_bot_api.push_message(
                    event.source.user_id,
                    TextSendMessage(text="❌ 系統發生未預期的錯誤，請檢查 Log。")
                )
                
        else:
            # Echo for non-maps messages (or help text)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="請分享 Google Maps 餐廳連結給我，我會幫您分析評論！\n(點選 Google Maps 餐廳頁面 > 分享 > 複製連結)")
            )

# This is important for Vercel
# Vercel looks for a variable named 'app'

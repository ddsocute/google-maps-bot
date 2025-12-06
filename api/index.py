import os
import sys
import requests

# Add the parent directory to sys.path so we can import modules from the root
# This is critical for Vercel to find 'modules' when running api/index.py
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Line Bot Configuration
CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')

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
        user_msg = event.message.text
        
        # 過濾太短的訊息
        if len(user_msg) < 2:
            return

        # A. 搜尋 Google Maps (只抓關鍵資料)
        gmaps_url = "https://places.googleapis.com/v1/places:searchText"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": GOOGLE_MAPS_API_KEY,
            "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.rating,places.userRatingCount,places.reviews"
        }
        
        # 強制加上 "餐廳" 關鍵字，避免抓到地標或奇怪的公司
        # 如果使用者輸入 "鼎泰豐"，會變成 "鼎泰豐 餐廳" 去搜
        search_query = f"{user_msg}" 
        
        data = {
            "textQuery": search_query, 
            "languageCode": "zh-TW",
            "maxResultCount": 1
        }

        try:
            gmaps_res = requests.post(gmaps_url, headers=headers, json=data)
            result = gmaps_res.json()

            if not result.get('places'):
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"找不到「{user_msg}」這家店，請試著輸入完整店名喔！"))
                return

            place = result['places'][0]
            shop_name = place.get('displayName', {}).get('text', '未知店家')
            rating = place.get('rating', 'N/A')
            rating_count = place.get('userRatingCount', 0)
            address = place.get('formattedAddress', '無地址')
            reviews_list = place.get('reviews', [])

            # 如果沒有評論
            if not reviews_list:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"🏠 {shop_name}\n目前 Google 上還沒有評論可以分析。"))
                return

            # 組合評論資料 (只取前 15 則，太多會爆 Token)
            reviews_text = ""
            for r in reviews_list[:15]:
                stars = r.get('rating', 0)
                text = r.get('text', {}).get('text', '').replace('\n', ' ')
                reviews_text += f"({stars}星) {text}\n"

        except Exception as e:
            print(f"Google Maps Error: {e}")
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="地圖大神迷路了，請稍後再試。"))
            return

        # B. 呼叫 AI (大腦升級版)
        # 這裡是最重要的 Prompt 修改！
        ai_prompt = f"""
        你是一位毒舌但公正的美食偵探。使用者想知道這家店值不值得去。
        
        店家：{shop_name} (評分：{rating} / {rating_count}則)
        
        請閱讀以下真實評論，並用「繁體中文」嚴格分析，只回答以下三個欄位：

        1. 【一句話懶人包】：
           這家店是在賣什麼的？適合什麼情境？(例如：適合聚餐的台式熱炒，但環境吵雜)
        
        2. 【真實性偵測】(最重要！)：
           是否有「打卡送肉」、「五星好評送小菜」、「評論送飲料」等洗評行為？
           - 若有：請用「⚠️ 警告」開頭，明確說出送什麼。
           - 若無：請回答「✅ 評論看起來是有機的」。
        
        3. 【必吃推薦】：
           從評論中挖掘網友重複提到的好吃菜色 (前 3 名)。
           - 若大家只說好吃但沒說菜名，請回答「無具體推薦」。

        評論內容：
        {reviews_text}
        """

        try:
            deepseek_url = "https://api.deepseek.com/chat/completions"
            ai_headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
            }
            ai_data = {
                "model": "deepseek-reasoner", # 使用最強的推論模型 (或 deepseek-chat)
                "messages": [
                    {"role": "user", "content": ai_prompt}
                ],
                "stream": False
            }

            ai_res = requests.post(deepseek_url, headers=ai_headers, json=ai_data)
            ai_json = ai_res.json()
            
            # 取得 AI 回覆
            if 'choices' in ai_json:
                analysis_result = ai_json['choices'][0]['message']['content']
            else:
                analysis_result = "AI 睡著了，沒有回傳分析結果。"

            # 最終回傳
            # 這裡不使用 Flex Message，先用純文字確保能顯示，這最穩
            final_reply = f"🏠 店名：{shop_name}\n⭐ 評分：{rating} ({rating_count}則)\n📍 地址：{address}\n\n{analysis_result}\n\n(分析基於 Google 最新評論)"
            
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=final_reply))

        except Exception as e:
            print(f"AI Error: {e}")
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="分析失敗，請稍後再試。"))

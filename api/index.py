import os
import sys
import requests
import re

# Add the parent directory to sys.path so we can import modules from the root
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

if not CHANNEL_ACCESS_TOKEN or not CHANNEL_SECRET:
    print('Warning: LINE_CHANNEL_ACCESS_TOKEN and LINE_CHANNEL_SECRET are missing.')

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN) if CHANNEL_ACCESS_TOKEN else None
handler = WebhookHandler(CHANNEL_SECRET) if CHANNEL_SECRET else None

@app.route("/callback", methods=['POST'])
def callback():
    if not handler:
        abort(500)
    
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@app.route("/health", methods=['GET'])
def health():
    return 'OK', 200

if handler:
    @handler.add(MessageEvent, message=TextMessage)
    def handle_message(event):
        user_msg = event.message.text.strip()
        
        if len(user_msg) < 2:
            return

        # 1. 檢查是否為網址 (URL)
        # Google Places API 用網址搜尋效果很差，容易抓錯。
        # 我們引導使用者輸入「店名」。
        if "http" in user_msg or "goo.gl" in user_msg or "google.com" in user_msg:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="💡 為了分析更準確，請直接輸入「餐廳名稱」給我！\n(例如：鼎泰豐 信義店)")
            )
            return

        # 2. 搜尋 Google Maps (用店名搜尋)
        # 加上 "餐廳" 關鍵字可以增加準確度，但有時候使用者找的不是餐廳，所以我們先試原名
        search_query = user_msg
        
        gmaps_url = "https://places.googleapis.com/v1/places:searchText"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": GOOGLE_MAPS_API_KEY,
            "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.rating,places.userRatingCount,places.reviews"
        }
        
        data = {
            "textQuery": search_query, 
            "languageCode": "zh-TW",
            "maxResultCount": 1
        }

        try:
            # 告訴使用者正在處理
            # (Reply Token 只能用一次，所以這裡不能先回覆，除非用 Push Message，但 Push 要錢)
            # 我們直接做完再回覆，因為 timeout 已經設長了。
            
            gmaps_res = requests.post(gmaps_url, headers=headers, json=data)
            result = gmaps_res.json()

            if not result.get('places'):
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"找不到「{user_msg}」，請確認店名正確喔！"))
                return

            place = result['places'][0]
            shop_name = place.get('displayName', {}).get('text', '未知店家')
            rating = place.get('rating', 'N/A')
            rating_count = place.get('userRatingCount', 0)
            address = place.get('formattedAddress', '無地址')
            reviews_list = place.get('reviews', [])

            if not reviews_list:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"🏠 {shop_name}\n這家店目前沒有評論可以分析。"))
                return

            # 組合評論資料 (取前 20 則)
            reviews_text = ""
            for r in reviews_list[:20]:
                stars = r.get('rating', 0)
                text = r.get('text', {}).get('text', '').replace('\n', ' ')
                reviews_text += f"({stars}星) {text}\n"

        except Exception as e:
            print(f"Google Maps Error: {e}")
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="地圖搜尋出錯了，請稍後再試。"))
            return

        # 3. 呼叫 AI (毒舌美食家 Prompt)
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
                "model": "deepseek-reasoner",
                "messages": [
                    {"role": "user", "content": ai_prompt}
                ],
                "stream": False
            }

            ai_res = requests.post(deepseek_url, headers=ai_headers, json=ai_data)
            ai_json = ai_res.json()
            
            if 'choices' in ai_json:
                analysis_result = ai_json['choices'][0]['message']['content']
            else:
                analysis_result = "AI 罷工了，沒有回傳結果。"

            final_reply = f"🏠 店名：{shop_name}\n⭐ 評分：{rating} ({rating_count}則)\n📍 地址：{address}\n\n{analysis_result}\n\n(分析基於 Google 最新評論)"
            
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=final_reply))

        except Exception as e:
            print(f"AI Error: {e}")
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="分析失敗，請稍後再試。"))

import os
import json
from openai import OpenAI

class AIAnalyzer:
    def __init__(self):
        api_key = os.getenv('DEEPSEEK_API_KEY')
        if not api_key:
            print("Warning: DEEPSEEK_API_KEY not found.")
            self.client = None
        else:
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://api.deepseek.com"
            )

    def analyze_reviews(self, reviews_data, restaurant_name="這家餐廳"):
        """
        Analyzes reviews using DeepSeek Reasoner to detect fake reviews and extract insights.
        """
        if not self.client:
            return {"error": "API Key 未設定 (DEEPSEEK_API_KEY)"}

        if not reviews_data:
            return {"error": "沒有足夠的評論資料進行分析。"}

        # Prepare the prompt
        reviews_text = ""
        for i, r in enumerate(reviews_data):
            reviews_text += f"{i+1}. [{r['rating']}星] {r['text']}\n"

        system_prompt = """
你是一個嚴格的美食偵探。你的任務是對餐廳評論進行深度推理分析，偵測洗評行為並挖掘真實特色。
請務必以 JSON 格式回傳結果。
"""

        user_prompt = f"""
以下是「{restaurant_name}」的 Google 評論原始資料：

{reviews_text}

請執行以下分析任務：

1. [洗評偵測]：嚴格檢查是否有「打卡」、「送肉」、「五星」、「優惠」、「贈送」、「招待」等關鍵字與高分評價同時出現的情況？
2. [菜色挖掘]：找出描述具體口感的評論，列出前 3 名最多人提到的必吃菜色。
3. [真實評價]：排除那些疑似洗評的評論後，你認為這家店的實際分數大概是多少？(原分參考用)
4. [一句話總結]：這家店適合什麼樣的人去？

請回傳純 JSON 格式，不要包含 markdown 標記：
{{
  "risk_level": "High/Medium/Low",
  "warning_message": "警告訊息或健康確認",
  "recommended_dishes": ["菜色1", "菜色2", "菜色3"],
  "real_score": 3.8,
  "reason": "評分理由",
  "summary": "一句話總結"
}}
"""
        try:
            response = self.client.chat.completions.create(
                model="deepseek-reasoner",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                stream=False
            )
            
            content = response.choices[0].message.content
            
            # Clean up markdown if present
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "")
            elif content.startswith("```"):
                content = content.replace("```", "")
                
            return json.loads(content.strip())
            
        except Exception as e:
            print(f"DeepSeek Analysis failed: {e}")
            return {
                "error": "AI 分析暫時無法使用，請稍後再試。",
                "details": str(e)
            }

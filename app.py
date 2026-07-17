import os
import json
import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# 🔐 從雲端保險箱讀取 API 金鑰
GEMINI_API_KEY = os.environ.get("OPENAI_API_KEY", "") 

DB_FILE = 'vocab_evolution_db.json'

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            try: 
                return json.load(f)
            except: 
                return []
    return []

def save_db(data):
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"資料庫寫入失敗: {str(e)}")

@app.route('/')
def index():
    vocab_list = load_db()
    return render_template('index.html', vocab_list=vocab_list)

@app.route('/analyze_word', methods=['POST'])
def analyze_word():
    word_input = request.json.get('word', '').strip().lower()
    if not word_input:
        return jsonify({"status": "error", "message": "請輸入英文單字"})

    if not GEMINI_API_KEY:
        return jsonify({"status": "error", "message": "後台尚未設定 API 金鑰！"})

    # 🎯 丟給 Gemini 的高階語言學提示詞 (強迫它只回傳純粹的 JSON)
    prompt = f"""
    你現在是頂級語言學家。請針對英文單字 "{word_input}" 進行深度的字根字首與詞源學拆解分析。
    必須嚴格且『只能』回傳以下規定的純 JSON 格式，不要包含任何 ```json 字樣或多餘的文字：
    {{
        "word": "{word_input}",
        "structure": "填寫單字的組成公式，例如：pro- (向前) + spect (看) + -ive (形容詞字尾)",
        "root_info": "說明這個單字的核心字根是哪一個，以及該字根的基本原始字義",
        "evolution": "用大約100字簡述這個字根從拉丁文、希臘文或古法文演變成現代英語的歷史與核心觀念演變",
        "derivatives": [
            {{"word": "衍生字1", "part": "詞性", "meaning": "中文解釋"}},
            {{"word": "衍生字2", "part": "詞性", "meaning": "中文解釋"}},
            {{"word": "衍生字3", "part": "詞性", "meaning": "中文解釋"}},
            {{"word": "衍生字4", "part": "詞性", "meaning": "中文解釋"}}
        ]
    }}
    """
    
    # 🚀 修正為 Google Gemini 官方標準通訊格式與網址
    url = f"https://googleapis.com{GEMINI_API_KEY}"
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }
    
    try:
        response = requests.post(url, json=payload, timeout=20)
        res_data = response.json()
        
        # 🔑 精準抓取 Google Gemini 的回傳文字
        ai_raw_text = res_data['candidates'][0]['content']['parts'][0]['text'].strip()
        
        # ✨ 完美修復字串清洗邏輯（剔除 markdown 標籤）
        if ai_raw_text.startswith("```"):
            lines = ai_raw_text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].startswith("```"):
                lines = lines[:-1]
            ai_raw_text = "\n".join(lines).strip()
            
        ai_data = json.loads(ai_raw_text)
        
        # 寫入本地 JSON 資料庫
        current_db = load_db()
        current_db.insert(0, ai_data)
        save_db(current_db)
        
        return jsonify({"status": "success", "data": ai_data})
    except Exception as e:
        # 如果還是失敗，會直接在網頁彈窗吐出具體原因
        return jsonify({"status": "error", "message": f"AI 引擎解析失敗: {str(e)}"})

if __name__ == '__main__':
    app.run(debug=True)

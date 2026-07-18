import os
import json
import requests  # 🚀 使用原生網路套件，免安裝任何 Google 複雜模組
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# 🔐 安全從雲端環境變數讀取你的 AQ 金鑰
GEMINI_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()

DB_FILE = 'vocab_evolution_db.json'

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            try: return json.load(f)
            except: return []
    return []

def save_db(data):
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except:
        pass

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

    # 🎯 丟給 Gemini 的高階語言學提示詞
    prompt = f"""
    你現在是頂級語言學家。請針對英文單字 "{word_input}" 進行深度的字根字首與詞源學拆解分析。
    必須嚴格且『只能』回傳以下規定的純 JSON 格式，不要包含任何 markdown 的 ```json 字樣或多餘文字：
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
    
    # 🚀 使用 Google 官方最穩定的原始通訊端點網址（能完美辨識 AQ 開頭金鑰）
    url = f"https://googleapis.com{GEMINI_API_KEY}"
    
    # 建立精準符合 Google 要求的資料結構
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "responseMimeType": "application/json"  # 強制 AI 輸出純 JSON
        }
    }
    
    try:
        response = requests.post(url, json=payload, timeout=20)
        res_data = response.json()
        
        # 爬梳 Google 原始回傳的 JSON 字串
        ai_raw_text = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
        ai_data = json.loads(ai_raw_text)
        
        # 寫入本地雲端 JSON 資料庫
        current_db = load_db()
        current_db.insert(0, ai_data)
        save_db(current_db)
        
        return jsonify({"status": "success", "data": ai_data})
    except Exception as e:
        return jsonify({"status": "error", "message": f"AI 大腦合體閃退，請確認 Render 金鑰是否填寫正確。原因: {str(e)}"})

if __name__ == '__main__':
    app.run(debug=True)

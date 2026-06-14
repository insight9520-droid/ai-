import json
import re
import random
import requests
from config import GROQ_API_KEYS, GEMINI_API_KEYS
from system_core import get_registered_actions

def get_system_prompt():
    actions_list = "\n".join([f"- {a}" for a in get_registered_actions()])
    return f"""
너는 'AI OS 에이전트'이다. 사용자의 Windows 시스템을 돕는 친절하고 유능한 비서처럼 행동하라.

[규칙]
1. 답변은 반드시 한국어로, 정중하고 친절하게 하라. (예: "~해드릴까요?", "~완료했습니다!")
2. 자신의 기능을 설명할 때는 'list_directory' 같은 기술적인 용어 대신 "파일 목록 보기", "시스템 상태 확인" 등 사용자가 이해하기 쉬운 용어를 사용하라.
3. 반드시 단 하나의 JSON 객체만 출력하라. 다른 텍스트는 섞지 마라.
4. 여러 작업 요청 시, 가장 중요한 첫 번째 작업부터 순차적으로 수행하라.

허용된 action 목록:
{actions_list}

출력 형식:
{{
  "action": "액션명",
  "target": "대상",
  "params": {{}},
  "response": "사용자에게 줄 친절한 답변 메시지"
}}
"""

def clean_json(text):
    try:
        text = re.sub(r"```json|```", "", text).strip()
        return json.loads(text)
    except:
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            try: return json.loads(match.group())
            except: pass
    return None

def ask_ai(user_input, feedback=None):
    prompt = get_system_prompt()
    full_input = f"{prompt}\n\n사용자: {user_input}"
    
    # 1. Groq 시도
    if GROQ_API_KEYS:
        for i, key in enumerate(GROQ_API_KEYS, 1):
            print(f"DEBUG: Groq {i}번 키 시도 중... ({key[:8]}...)")
            try:
                res = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {key}"},
                    json={
                        "model": "llama-3.3-70b-versatile",
                        "messages": [{"role": "user", "content": full_input}]
                    },
                    timeout=10
                )
                if res.status_code == 200:
                    print(f"✅ Groq {i}번 키로 성공!")
                    return clean_json(res.json()["choices"][0]["message"]["content"]), None
                else:
                    print(f"❌ Groq {i}번 키 실패: {res.status_code}")
            except Exception as e:
                print(f"❗ Groq {i}번 키 오류: {e}")

    # 2. Gemini 시도
    if GEMINI_API_KEYS:
        for i, key in enumerate(GEMINI_API_KEYS, 1):
            print(f"DEBUG: Gemini {i}번 키 시도 중... ({key[:8]}...)")
            url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={key}"
            try:
                res = requests.post(url, json={"contents": [{"parts": [{"text": full_input}]}]}, timeout=10)
                if res.status_code == 200:
                    print(f"✅ Gemini {i}번 키로 성공!")
                    return clean_json(res.json()["candidates"][0]["content"]["parts"][0]["text"]), None
                else:
                    print(f"❌ Gemini {i}번 키 실패: {res.status_code}")
            except Exception as e:
                print(f"❗ Gemini {i}번 키 오류: {e}")
            
    return None, "모든 API 키가 실패했습니다."

def handle_with_feedback(user_input):
    ai_data, error_msg = ask_ai(user_input)
    if ai_data: return ai_data
    return {"action": "none", "response": f"❌ {error_msg}"}

import re
from pathlib import Path

# .env 파일 경로 설정
env_path = Path(__file__).parent / ".env"

def load_keys_from_file():
    """ .env 파일 전체를 읽어서 키 패턴만 추출 """
    if not env_path.exists():
        print("⚠️ WARNING: .env 파일이 존재하지 않습니다!")
        return [], [], []

    content = env_path.read_text(encoding='utf-8')
    
    # 1. Groq 키 추출 (gsk_로 시작하는 40자 이상 문자열)
    groq_keys = re.findall(r"gsk_[a-zA-Z0-9]{40,}", content)
    
    # 2. Gemini 키 추출 (AIzaSy로 시작하는 30자 이상 문자열)
    gemini_keys = re.findall(r"AIzaSy[a-zA-Z0-9_-]{30,}", content)
    
    # 3. Tavily 키 추출 (tvly-로 시작하는 30자 이상 문자열)
    tavily_keys = re.findall(r"tvly-[a-zA-Z0-9]{30,}", content)
    
    # 중복 제거 및 디버깅 출력
    groq_keys = list(dict.fromkeys(groq_keys))
    gemini_keys = list(dict.fromkeys(gemini_keys))
    tavily_keys = list(dict.fromkeys(tavily_keys))
    
    print(f"DEBUG: Groq 키 {len(groq_keys)}개 발견")
    print(f"DEBUG: Gemini 키 {len(gemini_keys)}개 발견")
    
    return groq_keys, gemini_keys, tavily_keys

# 전역 변수로 키 설정
GROQ_API_KEYS, GEMINI_API_KEYS, TAVILY_KEYS = load_keys_from_file()

if not GROQ_API_KEYS and not GEMINI_API_KEYS:
    print("⚠️ WARNING: 유효한 API 키를 하나도 찾지 못했습니다. .env 파일을 확인하세요!")

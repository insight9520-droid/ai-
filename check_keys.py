import os
from dotenv import load_dotenv
from pathlib import Path

def check():
    env_path = Path(__file__).parent / ".env"
    print(f"1. .env 파일 경로: {env_path}")
    print(f"2. .env 파일 존재 여부: {env_path.exists()}")
    
    if env_path.exists():
        with open(env_path, 'r') as f:
            print(f"3. .env 파일 내용 미리보기:\n{f.read()[:50]}...")
            
    load_dotenv(dotenv_path=env_path)
    
    groq = os.getenv("GROQ_API_KEYS")
    gemini = os.getenv("GEMINI_API_KEYS")
    
    print("\n--- 로드 결과 ---")
    print(f"GROQ_API_KEYS: {'✅ 로드됨' if groq else '❌ 로드 안됨'}")
    print(f"GEMINI_API_KEYS: {'✅ 로드됨' if gemini else '❌ 로드 안됨'}")

if __name__ == "__main__":
    check()

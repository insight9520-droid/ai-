# AI OS Assistant (Refactored)

이 프로젝트는 AI가 Windows 시스템을 더 정확하게 제어할 수 있도록 함수 레지스트리와 피드백 루프를 적용하여 리팩토링되었습니다.

## 🚀 주요 특징
1. **함수 레지스트리 (Function Registry)**: `system_core.py`에 등록된 함수만 AI가 사용할 수 있도록 강제하여 실행 오류를 최소화합니다.
2. **피드백 루프 (Feedback Loop)**: AI가 잘못된 명령(Action)을 내리면 시스템이 오류 내용을 전달하여 AI가 스스로 수정하도록 유도합니다.
3. **환경 변수 관리**: `.env` 파일을 통해 API 키를 안전하게 관리합니다.
4. **Windows 최적화**: PowerShell 및 WMIC를 활용하여 Windows 시스템 정보를 정확하게 가져옵니다.

## 🛠 설치 및 실행
1. 필요한 패키지 설치:
   ```bash
   pip install psutil python-dotenv requests
   ```
2. `.env` 파일 설정:
   `.env.template`을 복사하여 `.env` 파일을 만들고 API 키를 입력하세요.
3. 실행:
   ```bash
   python main.py
   ```

## 📂 파일 구조
- `main.py`: UI 및 메인 로직 통합
- `ai_module.py`: AI 호출 및 피드백 루프 처리
- `system_core.py`: 시스템 명령 함수 및 레지스트리
- `config.py`: 환경 변수 및 설정 관리
- `.env`: API 키 저장 (사용자 생성 필요)

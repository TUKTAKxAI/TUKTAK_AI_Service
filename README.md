# TUKTAK_AI_Service

## AI Service 개발 환경 세팅 가이드

본 문서는 `TUKTAK_AI_Service` 프로젝트를 로컬에서 실행하기 위한 개발 환경 세팅 방법을 정리한 문서입니다.

---

## 1. Conda 가상환경 생성

Anaconda Prompt를 실행한 뒤 아래 명령어를 입력합니다.

```bash
conda create -n tuktak-ai python=3.11 pip -y
```

가상환경을 활성화합니다.

```bash
conda activate tuktak-ai
```

pip를 최신 버전으로 업데이트합니다.

```bash
python -m pip install --upgrade pip
```

Python 버전을 확인합니다.

```bash
python --version
```

정상적으로 설정되었다면 아래와 같이 출력됩니다.

```bash
Python 3.11.15
```

---

## 2. GitHub Repository Clone

CMD 또는 터미널을 열고, AI 서비스 레포지토리를 저장할 로컬 디렉토리로 이동합니다.

```bash
cd 본인이_AI_레포지토리를_넣을_로컬_디렉토리_주소
```

GitHub Repository를 clone합니다.

```bash
git clone https://github.com/TUKTAKxAI/TUKTAK_AI_Service.git
```

clone이 완료되면 프로젝트 폴더가 생성됩니다.

```bash
TUKTAK_AI_Service
```

---

## 3. VS Code에서 프로젝트 열기

VS Code를 실행한 뒤, 방금 clone한 `TUKTAK_AI_Service` 폴더를 엽니다.

또는 터미널에서 아래 명령어를 사용할 수 있습니다.

```bash
cd TUKTAK_AI_Service
code .
```

---

## 4. Python Interpreter 선택

VS Code에서 `main.py` 파일을 엽니다.

그다음 아래 순서대로 진행합니다.

1. `Ctrl + Shift + P` 입력
2. `Python: Select Interpreter` 검색 후 선택
3. 앞에서 생성한 Conda 가상환경인 `tuktak-ai` 선택

예시:

```bash
Python 3.11.x ('tuktak-ai': conda)
```

---

## 5. VS Code 터미널에서 가상환경 확인

VS Code 상단 메뉴에서 새 터미널을 엽니다.

```bash
Terminal > New Terminal
```

터미널 입력창 앞에 아래처럼 `(tuktak-ai)`가 표시되는지 확인합니다.

```bash
(tuktak-ai) C:\...\TUKTAK_AI_Service>
```

`(tuktak-ai)`가 보이면 정상적으로 가상환경이 적용된 상태입니다.

---

## 6. requirements.txt 설치

VS Code 터미널에서 아래 명령어를 실행합니다.

```bash
pip install -r requirements.txt
```

설치가 완료될 때까지 기다립니다.

설치가 정상적으로 완료되면 AI Service 개발 환경 세팅이 완료됩니다.

---

## 7. 설치 확인

필요한 주요 패키지가 정상 설치되었는지 확인합니다.

```bash
python -c "import fastapi; print('FastAPI OK')"
python -c "import langgraph; print('LangGraph OK')"
python -c "import langchain; print('LangChain OK')"
python -c "import chromadb; print('ChromaDB OK')"
```

각 명령어 실행 시 `OK`가 출력되면 정상입니다.

---

## 8. 서버 실행

개발 서버를 실행합니다.

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

서버 실행 후 아래 주소에 접속합니다.

```bash
http://localhost:8001/docs
```

Swagger 문서 화면이 보이면 정상적으로 실행된 것입니다.

---

## 9. 현재 구현된 API

```text
GET  /health
POST /api/v1/ai/estimates
POST /api/v1/ai/risk-reports
POST /api/v1/rag/documents
GET  /api/v1/rag/collections
```

견적 API 예시:

```bash
curl -X POST http://localhost:8001/api/v1/ai/estimates ^
  -H "Content-Type: application/json" ^
  -d "{\"description\":\"벽지가 찢어져서 부분 보수가 필요해요.\",\"image_urls\":[\"https://example.com/wallpaper.jpg\"]}"
```

현재는 실제 모델을 호출하지 않고 LangGraph mock 파이프라인으로 동작합니다.
확정되지 않은 기준값은 `app/core/constants.py`에 `TODO`와 `None`으로 분리했습니다.

---

## 10. AI 견적 파이프라인 MVP

현재 LangGraph 흐름:

```text
validate_input
→ check_image_quality
→ validate_text
→ analyze_text
→ lookup_base_price_rule
→ text_similarity_search 또는 text_and_image_similarity_search
→ evaluate_similar_cases
→ calculate_estimate_from_similar_cases 또는 calculate_estimate_with_base_price_and_llm
→ validate_estimate_result
```

초기 구현 원칙:

* 텍스트 유효성 검사는 임시 Rule Engine 구조만 둔다.
* 유사사례 검색은 ChromaDB 연결 전까지 빈 결과를 반환한다.
* 유사사례가 부족하면 `data/price_reference/base_price_table.sample.csv` 기준 단가표를 사용한다.
* 실제 임베딩 모델, 텍스트 분류 모델, Vision LLM은 추후 설정값과 서비스 파일에 연결한다.

---

## 11. 기준 단가표

샘플 단가표 위치:

```text
data/price_reference/base_price_table.sample.csv
```

운영용 단가표 후보:

```text
data/price_reference/base_price_table.csv
data/price_reference/base_price_table.xlsx
```

운영용 파일은 `.gitignore`에 포함되어 있고, 샘플 CSV만 커밋 대상으로 둡니다.

---

## 12. 테스트

의존성 설치 후 아래 명령으로 확인합니다.

```bash
pytest
```

간단 실행 확인:

```bash
python -m compileall app main.py
```

---

## 13. Main Backend 연결

백엔드 연결 지점은 `docs/backend-integration.md`에 정리했습니다.

핵심은 `TUKTAK_Backend`의 `app/services/ai_stub.py` 직접 호출을 `httpx` 기반 AI Service 클라이언트 호출로 교체하는 것입니다.

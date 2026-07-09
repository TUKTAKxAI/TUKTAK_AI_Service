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

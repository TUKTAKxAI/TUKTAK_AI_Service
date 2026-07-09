# Main Backend 연결 지점

현재 `TUKTAK_Backend`는 AI 서버를 직접 호출하지 않고 `app/services/ai_stub.py`로 DB 값을 채우고 있습니다.
AI Service가 준비되면 아래 파일을 중심으로 stub 호출을 HTTP 호출로 교체하면 됩니다.

## 1. 설정 추가

파일: `TUKTAK_Backend/app/core/settings.py`

추가 권장 설정:

```python
ai_service_url: str = Field("http://localhost:8001", alias="AI_SERVICE_URL")
ai_service_timeout_seconds: float = Field(30.0, gt=0, alias="AI_SERVICE_TIMEOUT_SECONDS")
```

백엔드 `.env` 예시:

```env
AI_SERVICE_URL=http://localhost:8001
AI_SERVICE_TIMEOUT_SECONDS=30
```

## 2. AI 견적 연결

파일: `TUKTAK_Backend/app/api/v1/routes/ai_estimates.py`

현재 흐름:

```python
from app.services import ai_stub
...
await ai_stub.complete_ai_estimate(estimate)
```

교체 방향:

1. `app/services/ai_service_client.py`를 만든다.
2. `POST {AI_SERVICE_URL}/api/v1/ai/estimates`를 호출한다.
3. AI Service 응답을 `AiEstimate` 모델 필드에 매핑한다.
4. 실패 응답이면 `estimate_status="FAILED"`와 실패 사유를 저장하거나 422를 반환한다.

AI Service 요청 JSON 예시:

```json
{
  "request_id": "estimate-1",
  "description": "벽지가 찢어져서 부분 보수가 필요해요.",
  "image_urls": ["/uploads/ai-estimates/1/example.jpg"],
  "main_category_hint": "INTERIOR"
}
```

AI Service 응답 매핑:

```text
estimate.main_category         <- estimate.main_category
estimate.object_label          <- estimate.object_label
estimate.problem_label         <- estimate.problem_label
estimate.repair_task_name      <- estimate.repair_task
estimate.min_price             <- estimate.expected_price_min
estimate.max_price             <- estimate.expected_price_max
estimate.estimated_minutes_min <- estimate.expected_duration_minutes
estimate.estimated_minutes_max <- estimate.expected_duration_minutes
estimate.confidence_score      <- estimate.confidence_score
estimate.ai_summary            <- warnings/missing_info 기반 요약
estimate.estimate_status       <- COMPLETED 또는 FAILED
```

## 3. 리스크 리포트 연결

파일: `TUKTAK_Backend/app/services/risk_report.py`

현재 흐름:

```python
from app.services import ai_stub
...
await ai_stub.complete_risk_report(db, risk_report)
```

교체 방향:

1. 생성된 `RiskReport`의 `estimate_id`로 `AiEstimate`를 조회한다.
2. `POST {AI_SERVICE_URL}/api/v1/ai/risk-reports`를 호출한다.
3. 응답의 `risk_report`를 `RiskReport` 모델 필드에 매핑한다.

## 4. 관리자 RAG 문서 연결

파일: `TUKTAK_Backend/app/api/v1/routes/admin_rag.py`

현재 흐름:

```python
db.add(await ai_stub.complete_rag_document(document))
```

교체 방향:

1. 백엔드는 문서 메타데이터와 업로드 파일 URL을 저장한다.
2. AI Service의 `POST /api/v1/rag/documents`로 문서 등록을 알린다.
3. 실제 문서 파싱, chunk, embedding, Chroma 저장은 AI Service가 담당한다.
4. 백엔드는 AI Service 처리 결과의 vector id 또는 상태만 저장한다.

## 5. 지금 당장 고치지 않은 이유

이번 단계의 목표는 AI Service의 `/health`와 mock LangGraph 견적 API를 먼저 안정화하는 것입니다.
백엔드 DB 모델과 화면 API는 이미 동작하는 stub 흐름이 있으므로, AI Service 런타임 검증 후 위 지점만 좁게 교체하는 편이 리스크가 낮습니다.


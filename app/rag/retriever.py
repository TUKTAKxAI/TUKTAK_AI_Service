from typing import Any


class RepairCaseRetriever:
    def search_text_cases(self, state: dict[str, Any], top_k: int) -> list[dict[str, Any]]:
        # TODO: ChromaDB repair_cases 컬렉션 연결.
        return []

    def search_text_and_image_cases(self, state: dict[str, Any], top_k: int) -> list[dict[str, Any]]:
        # TODO: 이미지 임베딩/유사도 정책 확정 후 ChromaDB 검색 연결.
        return self.search_text_cases(state, top_k)


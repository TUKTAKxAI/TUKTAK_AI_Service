from pathlib import Path

from app.rag.retriever import (
    RepairCaseRetriever,
    build_metadata_filter,
    get_image_similarity_category,
    get_image_similarity_threshold,
)


class FakeImageEmbeddingService:
    def embed_image_path(self, image_path: str) -> list[float]:
        return [1.0, 0.0, 0.0]


class FakeCollection:
    def __init__(self):
        self.last_get_where = None
        self.last_query_where = None

    def get(self, where, limit, include):
        self.last_get_where = where
        return {
            "ids": ["case-1"],
            "metadatas": [
                {
                    "main_category": "INTERIOR",
                    "object_label": "wall",
                    "problem_label": "crack",
                    "repair_task": "wall_crack_repair",
                    "price": 100000,
                    "duration_minutes": 90,
                }
            ],
            "documents": ["wall crack case"],
        }

    def query(self, query_embeddings, n_results, where, include):
        self.last_query_where = where
        return {
            "ids": [["case-pass", "case-fail"]],
            "metadatas": [[
                {
                    "main_category": "INTERIOR",
                    "object_label": "wall",
                    "problem_label": "crack",
                    "repair_task": "wall_crack_repair",
                    "price": 100000,
                    "duration_minutes": 90,
                },
                {
                    "main_category": "INTERIOR",
                    "object_label": "wall",
                    "problem_label": "crack",
                    "repair_task": "wall_crack_repair",
                    "price": 120000,
                    "duration_minutes": 100,
                },
            ]],
            "documents": [["pass case", "fail case"]],
            "distances": [[0.10, 0.30]],
        }


def test_build_metadata_filter_uses_structured_fields() -> None:
    state = {
        "main_category": "INTERIOR",
        "object_label": "wall",
        "problem_label": "crack",
        "repair_task": "wall_crack_repair",
    }

    assert build_metadata_filter(state) == {
        "$and": [
            {"main_category": "INTERIOR"},
            {"object_label": "wall"},
            {"problem_label": "crack"},
            {"repair_task": "wall_crack_repair"},
        ]
    }


def test_text_search_returns_metadata_only_cases() -> None:
    collection = FakeCollection()
    retriever = RepairCaseRetriever(collection=collection, image_embedding_service=FakeImageEmbeddingService())

    cases = retriever.search_text_cases(
        {
            "main_category": "INTERIOR",
            "object_label": "wall",
            "problem_label": "crack",
            "repair_task": "wall_crack_repair",
        },
        top_k=3,
    )

    assert collection.last_get_where is not None
    assert cases[0]["case_id"] == "case-1"
    assert cases[0]["price"] == 100000
    assert cases[0]["duration_minutes"] == 90


def test_image_search_filters_by_report_threshold(tmp_path: Path) -> None:
    image_path = tmp_path / "case.jpg"
    image_path.write_bytes(b"fake")
    collection = FakeCollection()
    retriever = RepairCaseRetriever(collection=collection, image_embedding_service=FakeImageEmbeddingService())

    cases = retriever.search_text_and_image_cases(
        {
            "main_category": "INTERIOR",
            "object_label": "wall",
            "problem_label": "crack",
            "repair_task": "wall_crack_repair",
            "image_paths": [str(image_path)],
            "image_similarity_category": "wall_crack",
        },
        top_k=3,
    )

    assert collection.last_query_where is not None
    assert [case["case_id"] for case in cases] == ["case-pass"]
    assert cases[0]["image_similarity"] == 0.9


def test_image_similarity_category_and_threshold_from_structured_labels() -> None:
    state = {
        "main_category": "INTERIOR",
        "object_label": "wall",
        "problem_label": "crack",
        "repair_task": "wall_crack_repair",
    }

    category = get_image_similarity_category(state)

    assert category == "wall_crack"
    assert get_image_similarity_threshold(category) == 0.833714

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.core.config import settings


SINGLE_LABEL_FIELDS = [
    "main_category",
    "object_label",
    "problem_label",
    "repair_task",
    "validity_label",
]
MULTI_LABEL_FIELD = "missing_info"
NO_MISSING_INFO_LABEL = "없음"


class NLPStructureService:
    def analyze(self, description: str) -> dict[str, Any]:
        runtime = _load_runtime()
        prediction = runtime.predict(description)
        missing_info = _split_missing_info(prediction[MULTI_LABEL_FIELD])

        return {
            "main_category": prediction["main_category"],
            "object_label": prediction["object_label"],
            "problem_label": prediction["problem_label"],
            "repair_task": prediction["repair_task"],
            "validity_label": prediction["validity_label"],
            "missing_info": missing_info,
            "nlp_structuring_result": {
                "model_name": settings.nlp_structuring_model_name,
                "raw_prediction": prediction,
                "raw_output": _format_prediction(prediction),
            },
        }


class _NLPStructureRuntime:
    def __init__(self) -> None:
        import torch
        import torch.nn as nn
        from safetensors.torch import load_file as load_safetensors
        from transformers import AutoConfig, AutoModel, AutoTokenizer

        self.torch = torch
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model_dir = Path(settings.nlp_structuring_model_path)
        self.label_maps = _load_json(self.model_dir / "label_maps.json")
        self.tokenizer = AutoTokenizer.from_pretrained(str(self.model_dir))

        class MultiTaskRepairClassifier(nn.Module):
            def __init__(self, model_dir: Path, label_maps: dict[str, dict[str, int]]) -> None:
                super().__init__()
                encoder_config = AutoConfig.from_pretrained(str(model_dir))
                self.encoder = AutoModel.from_config(encoder_config)
                hidden_size = self.encoder.config.hidden_size
                self.dropout = nn.Dropout(0.1)
                self.single_heads = nn.ModuleDict(
                    {
                        field: nn.Linear(hidden_size, len(label_maps[field]))
                        for field in SINGLE_LABEL_FIELDS
                    }
                )
                self.missing_info_head = nn.Linear(hidden_size, len(label_maps[MULTI_LABEL_FIELD]))

            def forward(self, input_ids=None, attention_mask=None, token_type_ids=None, **kwargs):
                encoder_inputs = {"input_ids": input_ids, "attention_mask": attention_mask}
                if token_type_ids is not None:
                    encoder_inputs["token_type_ids"] = token_type_ids

                outputs = self.encoder(**encoder_inputs)
                if hasattr(outputs, "pooler_output") and outputs.pooler_output is not None:
                    pooled = outputs.pooler_output
                else:
                    pooled = outputs.last_hidden_state[:, 0]
                pooled = self.dropout(pooled)

                logits = {
                    f"{field}_logits": head(pooled)
                    for field, head in self.single_heads.items()
                }
                logits[f"{MULTI_LABEL_FIELD}_logits"] = self.missing_info_head(pooled)
                return logits

        self.model = MultiTaskRepairClassifier(
            self.model_dir,
            self.label_maps,
        )

        safetensor_path = self.model_dir / "model.safetensors"
        bin_path = self.model_dir / "pytorch_model.bin"
        if safetensor_path.exists():
            state_dict = load_safetensors(str(safetensor_path))
        elif bin_path.exists():
            state_dict = torch.load(bin_path, map_location="cpu")
        else:
            raise FileNotFoundError(f"No NLP structuring model weights found in {self.model_dir}")

        self.model.load_state_dict(state_dict, strict=False)
        self.model.to(self.device)
        self.model.eval()

    def predict(self, text: str) -> dict[str, str]:
        inputs = self.tokenizer(
            text,
            truncation=True,
            padding="max_length",
            max_length=settings.nlp_structuring_max_length,
            return_tensors="pt",
        )
        inputs = {key: value.to(self.device) for key, value in inputs.items()}

        with self.torch.no_grad():
            outputs = self.model(**inputs)

        prediction = {}
        for field in SINGLE_LABEL_FIELDS:
            idx_to_label = {idx: label for label, idx in self.label_maps[field].items()}
            idx = self.torch.argmax(outputs[f"{field}_logits"], dim=-1).item()
            prediction[field] = idx_to_label[idx]

        missing_idx_to_label = {
            idx: label for label, idx in self.label_maps[MULTI_LABEL_FIELD].items()
        }
        probs = self.torch.sigmoid(outputs[f"{MULTI_LABEL_FIELD}_logits"])[0]
        selected = (probs >= settings.nlp_structuring_missing_threshold).nonzero(as_tuple=True)[0].tolist()
        if not selected:
            selected = [int(self.torch.argmax(probs).item())]
        prediction[MULTI_LABEL_FIELD] = "|".join(missing_idx_to_label[idx] for idx in selected)
        return prediction


@lru_cache(maxsize=1)
def _load_runtime() -> _NLPStructureRuntime:
    return _NLPStructureRuntime()


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _split_missing_info(value: str | None) -> list[str]:
    labels = [item.strip() for item in (value or "").split("|") if item.strip()]
    return [label for label in labels if label != NO_MISSING_INFO_LABEL]


def _format_prediction(prediction: dict[str, str]) -> str:
    return ";\n".join(
        f"{field}={prediction.get(field, '')}"
        for field in SINGLE_LABEL_FIELDS + [MULTI_LABEL_FIELD]
    )

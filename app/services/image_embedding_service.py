from functools import lru_cache
from pathlib import Path

from app.core.config import settings


class ImageEmbeddingService:
    def embed_image_path(self, image_path: str) -> list[float]:
        runtime = _load_runtime()
        return runtime.embed_image_path(image_path)


class _NomicVisionRuntime:
    def __init__(self) -> None:
        import torch
        import torch.nn.functional as F
        from PIL import Image
        from transformers import AutoImageProcessor, AutoModel

        self.torch = torch
        self.functional = F
        self.image_cls = Image
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.processor = AutoImageProcessor.from_pretrained(settings.image_embedding_model_name)
        self.model = AutoModel.from_pretrained(
            settings.image_embedding_model_name,
            trust_remote_code=True,
        )
        self.model.to(self.device)
        self.model.eval()

    def embed_image_path(self, image_path: str) -> list[float]:
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image path does not exist: {image_path}")

        image = self.image_cls.open(path).convert("RGB")
        inputs = self.processor(image, return_tensors="pt")
        inputs = {key: value.to(self.device) for key, value in inputs.items()}

        with self.torch.no_grad():
            model_output = self.model(**inputs)

        image_embedding = model_output.last_hidden_state[:, 0]
        image_embedding = self.functional.normalize(image_embedding, p=2, dim=1)
        return image_embedding[0].detach().cpu().tolist()


@lru_cache(maxsize=1)
def _load_runtime() -> _NomicVisionRuntime:
    return _NomicVisionRuntime()

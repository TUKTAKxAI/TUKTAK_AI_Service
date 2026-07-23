from app.core.config import settings


def select_torch_device(torch):
    requested = settings.ai_torch_device.strip().lower()
    if requested in {"", "auto"}:
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if requested == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("AI_TORCH_DEVICE=cuda was requested, but CUDA is not available.")
    if requested not in {"cuda", "cpu"}:
        raise ValueError("AI_TORCH_DEVICE must be one of: auto, cuda, cpu.")
    return torch.device(requested)

def split_plain_text(content: str, chunk_size: int = 1000) -> list[str]:
    return [content[index : index + chunk_size] for index in range(0, len(content), chunk_size)]


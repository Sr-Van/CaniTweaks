"""Funções puras de formatação de valores para exibição."""


def format_bytes(size: int) -> str:
    """Converte bytes em texto legível (ex.: 1536 -> '1,5 KB')."""
    value = float(size)
    for unit in ("B", "KB", "MB"):
        if value < 1024:
            decimals = 0 if unit == "B" else 1
            return f"{value:.{decimals}f} {unit}".replace(".", ",")
        value /= 1024
    return f"{value:.1f} GB".replace(".", ",")

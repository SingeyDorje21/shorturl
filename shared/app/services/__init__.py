# Shuffled base-62 alphabet — changing this breaks existing short codes
BASE62 = "7aZ6DXsMn1Jo9GkbWTqc4zdrueQ5iL3ylwP2f8VtAhBjRKEmNOFpUvI0YxHSgC"

# Offset pushes all IDs above a minimum length so code "1" never appears
OFFSET = 20_000_000


def base62_encode(id: int) -> str:
    """Encode a positive integer into a short base-62 string."""
    n = id + OFFSET
    if n == 0:
        return BASE62[0]
    chars: list[str] = []
    while n > 0:
        chars.append(BASE62[n % 62])
        n //= 62
    return "".join(reversed(chars))


def base62_decode(code: str) -> int:
    """Decode a base-62 string back to the original integer (minus offset)."""
    alphabet_map = {ch: i for i, ch in enumerate(BASE62)}
    n = 0
    for ch in code:
        n = n * 62 + alphabet_map[ch]
    return n - OFFSET

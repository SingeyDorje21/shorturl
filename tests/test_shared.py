import pytest
from shared.app.services import base62_encode, base62_decode


def test_encode_is_deterministic():
    assert base62_encode(1) == base62_encode(1)


def test_encode_decode_roundtrip():
    for i in [1, 42, 1000, 99999, 1_000_000]:
        assert base62_decode(base62_encode(i)) == i


def test_different_ids_produce_different_codes():
    codes = {base62_encode(i) for i in range(1, 100)}
    assert len(codes) == 99


def test_offset_ensures_minimum_length():
    # With OFFSET=20_000_000, even id=1 should produce a multi-char code
    code = base62_encode(1)
    assert len(code) >= 4


def test_encode_only_uses_base62_alphabet():
    from shared.app.services import BASE62
    for i in [0, 1, 61, 62, 1000, 20_000_001]:
        code = base62_encode(i)
        for ch in code:
            assert ch in BASE62, f"Unexpected character {ch!r} in code {code!r}"

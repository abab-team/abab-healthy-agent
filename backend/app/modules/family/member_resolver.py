from __future__ import annotations


REFERENCE_ALIASES: dict[str, list[str]] = {
    "self": ["我", "我自己", "本人"],
    "father": ["爸爸", "我爸", "父亲"],
    "mother": ["妈妈", "我妈", "母亲"],
    "spouse": ["配偶", "老婆", "老公"],
}


def normalize_member_reference(member_reference: str) -> str:
    return member_reference.strip()


def relationship_labels_for_reference(member_reference: str) -> list[str]:
    normalized = normalize_member_reference(member_reference)
    if normalized in REFERENCE_ALIASES["father"]:
        return ["爸爸", "父亲"]
    if normalized in REFERENCE_ALIASES["mother"]:
        return ["妈妈", "母亲"]
    if normalized in REFERENCE_ALIASES["spouse"]:
        return ["配偶", "老婆", "老公"]
    return [normalized]


def is_self_reference(member_reference: str) -> bool:
    return normalize_member_reference(member_reference) in REFERENCE_ALIASES["self"]

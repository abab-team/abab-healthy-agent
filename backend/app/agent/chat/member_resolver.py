from __future__ import annotations


SELF_KEYWORDS = ("我", "本人", "自己", "my", "me")
FATHER_KEYWORDS = ("爸爸", "我爸", "父亲", "老爸", "father", "dad")
MOTHER_KEYWORDS = ("妈妈", "我妈", "母亲", "老妈", "mother", "mom")


def resolve_member_label(message: str) -> tuple[str | None, str]:
    text = (message or "").lower()
    if any(keyword in text for keyword in FATHER_KEYWORDS):
        return "爸爸", "family"
    if any(keyword in text for keyword in MOTHER_KEYWORDS):
        return "妈妈", "family"
    if any(keyword in text for keyword in SELF_KEYWORDS):
        return "我", "self"
    return None, "self"

import re

WORD_SPLIT_RE = re.compile(r"[A-Z\d]?[a-z\d]+|[A-Z\d]+(?![a-z])")


def capitalize(s: str) -> str:
    words = WORD_SPLIT_RE.findall(s)
    return "".join(word.capitalize() for word in words)

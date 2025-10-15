import re

WORD_SPLIT_RE = re.compile(r"[A-Z\d]?[a-z\d]+|[A-Z\d]+(?![a-z])")


def pascalize(s: str) -> str:
    words = WORD_SPLIT_RE.findall(s)
    return "".join(word.capitalize() for word in words)


def camelize(s: str) -> str:
    words = WORD_SPLIT_RE.findall(s)
    return "".join(
        [word.lower() for word in words[:1]] + [word.capitalize() for word in words[1:]]
    )

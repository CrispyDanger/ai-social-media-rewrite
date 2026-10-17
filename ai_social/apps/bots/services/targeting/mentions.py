import re

HANDLE_PATTERN = re.compile(r'(?<![A-Za-z0-9_])@([A-Za-z0-9_]{1,15})(?![A-Za-z0-9_])')


def extract_handles(text: str) -> set[str]:
    return {handle.lower() for handle in HANDLE_PATTERN.findall(text)}

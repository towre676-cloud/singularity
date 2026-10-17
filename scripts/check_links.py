#!/usr/bin/env python3
"""Check published relative links, locally or against a GitHub recursive tree.

Defaults to README.md and docs/MONOGRAPH.md. This checks file targets, not
fragment identifiers, external services, or the rendering of linked HTML.
Fenced code, inline code and mathematical notation are excluded from parsing.
"""
import argparse
import json
from pathlib import Path
import posixpath
import re
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DOCUMENTS = ("README.md", "docs/MONOGRAPH.md")


def blank(match):
    """Preserve offsets and line numbers when hiding non-Markdown material."""
    text = match.group() if hasattr(match, "group") else match
    return "".join("\n" if char == "\n" else " " for char in text)


def visible_markdown(source):
    lines = []
    fence = None
    for line in source.splitlines(keepends=True):
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if fence:
            lines.append(blank(line))
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence):
                fence = None
        elif marker:
            fence = marker[1]
            lines.append(blank(line))
        else:
            lines.append(line)
    text = "".join(lines)
    text = re.sub(r"<!--[\s\S]*?-->", blank, text)
    text = re.sub(r"(`+)[\s\S]*?\1", blank, text)
    text = re.sub(
        r"\\\([\s\S]*?\\\)|\\\[[\s\S]*?\\\]"
        r"|(?<!\\)\$\$[\s\S]*?(?<!\\)\$\$"
        r"|(?<!\\)\$(?!\$)[^\n]*?(?<!\\)\$",
        blank,
        text,
    )
    return text


def inline_destination(text, start):
    """Read a destination after ](, allowing nested or escaped parentheses."""
    if start >= len(text):
        return None
    if text[start] == "<":
        end = text.find(">", start + 1)
        return text[start + 1:end] if end != -1 else None
    depth = 0
    index = start
    while index < len(text):
        char = text[index]
        if char == "\\" and index + 1 < len(text):
            index += 2
            continue
        if char == "(" :
            depth += 1
        elif char == ")":
            if depth == 0:
                return text[start:index]
            depth -= 1
        elif char.isspace() and depth == 0:
            return text[start:index]
        index += 1
    return None


def link_targets(source):
    text = visible_markdown(source)
    label = r"(?:\\.|[^\]\\\n])*"
    for match in re.finditer(r"(?<!\\)!?\[" + label + r"\]\(\s*", text):
        target = inline_destination(text, match.end())
        if target:
            yield target, source.count("\n", 0, match.start()) + 1
    references = {}
    for match in re.finditer(r"^ {0,3}\[([^\]\n]+)\]:\s*(<[^>]+>|\S+)", text, re.M):
        references[" ".join(match[1].casefold().split())] = match[2].strip("<>")
    for match in re.finditer(r"(?<!\\)!?\[(" + label + r")\]\[([^\]\n]*)\]", text):
        identifier = " ".join((match[2] or match[1]).casefold().split())
        if identifier in references:
            yield references[identifier], source.count("\n", 0, match.start()) + 1


def relative_path(document, target):
    target = re.sub(r"\\([\\`*{}\[\]()#+.!_<> -])", r"\1", target)
    url = urlsplit(target)
    if url.scheme or url.netloc or not url.path or url.path.startswith("/"):
        return None
    return posixpath.normpath(posixpath.join(posixpath.dirname(document), unquote(url.path)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("documents", nargs="*", default=list(DEFAULT_DOCUMENTS),
                        help="repository-relative Markdown files")
    parser.add_argument("--tree-json", type=Path,
                        help="GitHub recursive-tree JSON; check remote target membership")
    arguments = parser.parse_args()
    remote = None
    if arguments.tree_json:
        try:
            payload = json.loads(arguments.tree_json.read_text())
            if payload.get("truncated"):
                raise ValueError("GitHub tree is truncated; absence cannot establish a broken link")
            if not isinstance(payload.get("tree"), list):
                raise ValueError("expected a GitHub tree response containing a 'tree' array")
            remote = {entry["path"] for entry in payload["tree"]}
        except (OSError, ValueError, KeyError, TypeError) as error:
            parser.error(str(error))
    checked = 0
    missing = []
    for document in arguments.documents:
        path = ROOT / document
        if not path.is_file():
            missing.append({"document": document, "error": "source document does not exist"})
            continue
        if remote is not None and document not in remote:
            missing.append({"document": document, "error": "document absent from remote tree"})
        for target, line in link_targets(path.read_text()):
            resolved = relative_path(document, target)
            if resolved is None:
                continue
            checked += 1
            exists = resolved in remote if remote is not None else (ROOT / resolved).exists()
            if not exists:
                missing.append({"document": document, "line": line,
                                "target": target, "resolved_path": resolved,
                                "error": "target absent from remote tree" if remote is not None
                                else "target does not exist"})
    print(json.dumps({"status": "failed" if missing else "passed",
                      "mode": "remote-tree" if remote is not None else "local",
                      "checked_relative_targets": checked, "missing": missing}, indent=2))
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())

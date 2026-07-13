"""Reorder the Featured builds cards in README.md by GitHub star count (desc).

Ties and API failures never scramble the list: sorting is stable, and any
failed star lookup aborts without touching the file.
"""
import json
import os
import re
import sys
import urllib.request

PATH = "README.md"
START = "<!-- FEATURED:START -->"
END = "<!-- FEATURED:END -->"

text = open(PATH, encoding="utf-8").read()
try:
    s = text.index(START)
    e = text.index(END)
except ValueError:
    print("featured markers not found, nothing to do")
    sys.exit(0)

section = text[s + len(START):e]
items = re.findall(r"(<!-- FEATURED-ITEM:([\w.-]+) -->.*?<!-- /FEATURED-ITEM -->)", section, re.S)
if len(items) < 2:
    print("fewer than 2 featured items, nothing to sort")
    sys.exit(0)

owner = os.environ.get("GITHUB_REPOSITORY_OWNER", "Alxve99")
token = os.environ.get("GITHUB_TOKEN", "")


def stars(repo: str):
    req = urllib.request.Request(f"https://api.github.com/repos/{owner}/{repo}")
    req.add_header("Accept", "application/vnd.github+json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp).get("stargazers_count", 0)
    except Exception as exc:  # noqa: BLE001
        print(f"warn: could not fetch stars for {repo}: {exc}", file=sys.stderr)
        return None


counts = {repo: stars(repo) for _, repo in items}
if any(v is None for v in counts.values()):
    print("star lookup failed, leaving order unchanged")
    sys.exit(0)

ordered = sorted(items, key=lambda item: -counts[item[1]])
sep = "\n\n<br/>\n<br/>\n\n"
new_section = "\n\n" + sep.join(block for block, _ in ordered) + "\n\n"
new_text = text[: s + len(START)] + new_section + text[e:]

if new_text != text:
    with open(PATH, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(new_text)
    print("reordered: " + ", ".join(f"{repo}={counts[repo]}" for _, repo in ordered))
else:
    print("order unchanged: " + ", ".join(f"{repo}={counts[repo]}" for _, repo in ordered))

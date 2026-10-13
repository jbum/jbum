#!/usr/bin/env python3
"""Rewrite two parts of README.md from GitHub:
- between the FEATURED markers, the repositories named in .github/featured.json, in its order, each
  with its own text (or, if that is empty, its GitHub description). One that isn't public yet is left
  out until it is, so a repo can be listed there before it launches.
- between the REPOS markers, a table of every public repository the user owns (forks left out), with
  its description and website as set on GitHub.
Run by .github/workflows/repos.yml; GH_TOKEN (optional locally) raises the API rate limit."""
import json, os, re, urllib.request

USER = "jbum"
HERE = os.path.dirname(__file__)
README = os.path.join(HERE, "..", "..", "README.md")
FEATURED = os.path.join(HERE, "..", "featured.json")

def repos():
    out, page = [], 1
    while True:
        req = urllib.request.Request(
            f"https://api.github.com/users/{USER}/repos?type=owner&per_page=100&page={page}",
            headers={"Accept": "application/vnd.github+json", "User-Agent": "profile-readme"})
        if os.environ.get("GH_TOKEN"):
            req.add_header("Authorization", "Bearer " + os.environ["GH_TOKEN"])
        batch = json.load(urllib.request.urlopen(req))
        out += batch
        if len(batch) < 100:
            return out
        page += 1

def cell(s):
    return (s or "").replace("|", "\\|").replace("\n", " ").strip()

def featured(public):
    by_name = {r["name"].lower(): r for r in public}
    lines = []
    for f in json.load(open(FEATURED, encoding="utf-8")):
        r = by_name.get(f["name"].lower())
        if r:
            lines.append(f"- [{r['name']}]({r['html_url']}) - {f.get('text') or cell(r['description'])}")
    return "\n".join(lines)

def table(public):
    rows = ["| Repository | Description | Site |", "| --- | --- | --- |"]
    for r in sorted(public, key=lambda r: r["name"].lower()):
        site = r.get("homepage") or ""
        site = f"[{re.sub(r'^https?://|/$', '', site)}]({site})" if site else ""
        rows.append(f"| [{r['name']}]({r['html_url']}) | {cell(r['description'])} | {site} |")
    return "\n".join(rows)

def fill(text, marker, body):
    start, end = f"<!-- {marker}:START -->", f"<!-- {marker}:END -->"
    a, b = text.index(start) + len(start), text.index(end)
    return text[:a] + "\n" + body + "\n" + text[b:]

public = [r for r in repos() if not r["fork"] and not r["private"]]
text = open(README, encoding="utf-8").read()
new = fill(fill(text, "FEATURED", featured(public)), "REPOS", table(public))
if new != text:
    open(README, "w", encoding="utf-8").write(new)
    print("README.md updated")
else:
    print("no change")

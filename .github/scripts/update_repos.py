#!/usr/bin/env python3
"""Rewrite the table between the REPOS markers in README.md from GitHub: every public repository
the user owns (forks left out), with its description and website as set on GitHub.
Run by .github/workflows/repos.yml; GH_TOKEN (optional locally) raises the API rate limit."""
import json, os, re, urllib.request

USER = "jbum"
README = os.path.join(os.path.dirname(__file__), "..", "..", "README.md")
START, END = "<!-- REPOS:START -->", "<!-- REPOS:END -->"

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

def table():
    rows = ["| Repository | Description | Site |", "| --- | --- | --- |"]
    for r in sorted((r for r in repos() if not r["fork"] and not r["private"]), key=lambda r: r["name"].lower()):
        site = r.get("homepage") or ""
        site = f"[{re.sub(r'^https?://|/$', '', site)}]({site})" if site else ""
        rows.append(f"| [{r['name']}]({r['html_url']}) | {cell(r['description'])} | {site} |")
    return "\n".join(rows)

text = open(README, encoding="utf-8").read()
a, b = text.index(START) + len(START), text.index(END)
new = text[:a] + "\n" + table() + "\n" + text[b:]
if new != text:
    open(README, "w", encoding="utf-8").write(new)
    print("README.md updated")
else:
    print("no change")

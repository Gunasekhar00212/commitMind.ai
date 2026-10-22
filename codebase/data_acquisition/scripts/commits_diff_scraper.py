import argparse
import json
import math
import os
import re
from pathlib import Path

import requests
from urllib3.util.retry import Retry

API = 'https://api.github.com/repos'
Token = os.getenv('GITHUB_TOKEN')
OUTPUT = Path(__file__).resolve().parents[3] / "knowledge/raw_data/commits_diff_data.jsonl"

parser = argparse.ArgumentParser()
parser.add_argument("repos", nargs="+", help="owner/name, one or more")
parser.add_argument("--target", type=int, default=500, help="stop after this many saved records")
parser.add_argument("--pages", type=int, default=50, help="max pages (100 commits each) per repo")
args = parser.parse_args()
REPOS, TARGET, PAGES = args.repos, args.target, args.pages

MAX_DIFF_CHARS = 12_000
SECRET = re.compile(
    r"(?i)(api[_-]?key|secret|password|access[_-]?token)\s*[:=]\s*['\"][^'\"]+"
)

session = requests.Session()
session.headers['Accept'] = 'application/vnd.github.v3+json'
if Token:
    session.headers['Authorization'] = f'token {Token}'
adapter = requests.adapters.HTTPAdapter(
    max_retries=Retry(total=5, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])
)
session.mount("https://", adapter)


def get(path, **params):
    r = session.get(f"{API}/{path}", params=params, timeout=10)
    r.raise_for_status()
    return r.json()


def collect():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    seen = set()
    if OUTPUT.exists():
        with OUTPUT.open('r', encoding='utf-8') as f:
            seen = {json.loads(line)['sha'] for line in f}
    saved = 0
    with OUTPUT.open('a', encoding='utf-8') as out:
        for repo in REPOS:
            looked = hits = 0
            for page in range(1, PAGES + 1):
                items = get(f"{repo}/commits", page=page, per_page=100)
                if not items:
                    break
                for item in items:
                    if saved >= TARGET:
                        break
                    if item['sha'] in seen:
                        continue
                    looked += 1
                    msg = item['commit']['message'].strip()
                    if len(item["parents"]) != 1 or not msg or '\n' in msg:
                        continue
                    files = get(f"{repo}/commits/{item['sha']}").get('files', [])
                    if not files or not all(
                        f['filename'].endswith('.py') and f['status'] != 'renamed' and f.get('patch')
                        for f in files
                    ):
                        continue
                    diff = "\n".join(
                        f"diff --git a/{f['filename']} b/{f['filename']}\n"
                        f"--- a/{f['filename']}\n+++ b/{f['filename']}\n{f['patch']}"
                        for f in files
                    )
                    if len(diff) > MAX_DIFF_CHARS or SECRET.search(diff):
                        continue
                    out.write(json.dumps({
                        "repo": repo,
                        "sha": item['sha'],
                        "message": msg,
                        "diff": diff,
                        "files": [f["filename"] for f in files],
                        "source_url": item["html_url"],
                    }, ensure_ascii=False) + "\n")
                    hits += 1
                    saved += 1
                if saved >= TARGET:
                    break
            rate = hits / looked if looked else 0
            need = math.ceil(TARGET / (rate * 100)) if rate else "inf"
            print(f"{repo}: looked {looked}, saved {hits}, pass {rate:.1%}, "
                  f"pages needed for {TARGET}: {need}")
            if saved >= TARGET:
                break
    return saved


if __name__ == "__main__":
    print(f"Saved {collect()} records to {OUTPUT}")
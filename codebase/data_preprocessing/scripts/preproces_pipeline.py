import json
from pathlib import Path
input = OUTPUT = Path(__file__).resolve().parents[3] / "knowledge/raw_data/commits_diff_data.jsonl"
with input.open('r', encoding='utf-8') as f:
    for line in f:
        data = json.loads(line)
        print(data['sha'])
        break


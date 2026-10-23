
import json
from collections import Counter
from statistics import mean, median
from pathlib import Path
first_words, lengths = Counter(), []
input = Path(__file__).resolve().parents[3] / "knowledge/raw_data/commits_diff_data.jsonl"
with open(input, encoding="utf-8") as f:
    for line in f:
        if not line.strip():
            continue
        msg = json.loads(line).get("message")
        if not isinstance(msg, str) or not msg.strip():
            continue
        first_words[msg.split()[0].lower()] += 1
        wordList = msg.split()
        lengths.append(len(wordList))

with open("message_analysis.txt", "w", encoding="utf-8") as out:
    out.write("First words (count):\n")
    for w, n in first_words.most_common():
        out.write(f"{w}: {n}\n")
    out.write(f"\nMessages: {len(lengths)}\n no.of words: min={min(lengths)} max={max(lengths)} mean={mean(lengths):.1f} median={median(lengths)}\n")

#!/usr/bin/env python3
"""科武纪元 RAG 查询工具 - 从硬科学素材库中检索相关内容。"""
import json, math, re, sys
from pathlib import Path
from collections import Counter
import numpy as np

BASE = Path("/workspace/科武纪元")
INDEX_DIR = BASE / "rag_kb" / "science" / "index"
CARDS = BASE / "rag_kb" / "science" / "cards" / "science_cards.jsonl"

# Load index
vectors_norm = np.load(INDEX_DIR / "tfidf_vectors.npy")
with open(INDEX_DIR / "vocab.json") as f:
    vocab = json.load(f)
with open(INDEX_DIR / "index_meta.json") as f:
    meta = json.load(f)
vocab_size = meta["vocab_size"]
N = meta["num_docs"]

# Build doc_freq from vectors (approximate via presence)
doc_freq = Counter()
with open(CARDS) as f:
    all_cards = [json.loads(l) for l in f if l.strip()]
trusted = [c for c in all_cards if c["trust"] in ("A", "B")]

def tokenize(text):
    tokens = []
    for seg in re.findall(r'[\u4e00-\u9fff]+', text):
        for i in range(len(seg) - 1):
            tokens.append(seg[i:i+2])
        if len(seg) >= 3:
            tokens.append(seg[:3])
        if len(seg) >= 4:
            tokens.append(seg[:4])
    tokens.extend(re.findall(r'[a-zA-Z]{3,}', text.lower()))
    tokens.extend(re.findall(r'\d+\.?\d*[万亿千百]?[度瓦伏特焦]?[时秒年]?', text))
    return tokens

# Rebuild doc_freq properly
doc_freq = Counter()
doc_tokens_list = []
for c in trusted:
    text = f"{c['title']} {' '.join(c.get('domains', []))} {c.get('content', '')[:1000]}"
    toks = tokenize(text)
    doc_tokens_list.append(toks)
    for t in set(toks):
        doc_freq[t] += 1

def search(query, top_k=5):
    q_toks = tokenize(query)
    q_vec = np.zeros(vectors_norm.shape[1], dtype=np.float32)
    tf = Counter(q_toks)
    for t, count in tf.items():
        if t in vocab:
            j = vocab[t]
            q_vec[j] = (1 + math.log(count)) * math.log(N / doc_freq.get(t, 1))
    norm = np.linalg.norm(q_vec)
    if norm > 0:
        q_vec /= norm
    scores = vectors_norm @ q_vec
    top_idx = np.argsort(scores)[::-1][:top_k]
    results = []
    for idx in top_idx:
        if scores[idx] > 0.01:
            card = trusted[idx]
            results.append({
                "id": card["id"],
                "trust": card["trust"],
                "source": card["source"],
                "title": card["title"][:80],
                "domains": card.get("domains", [])[:3],
                "score": round(float(scores[idx]), 4),
                "content_preview": card.get("content", "")[:300],
            })
    return results

if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "量子计算"
    results = search(query, top_k=5)
    print(f"查询: {query}")
    print(f"命中: {len(results)} 条\n")
    for r in results:
        print(f"[{r['trust']}] {r['score']:.3f} | {r['title']}")
        print(f"  来源: {r['source']} | 领域: {','.join(r['domains'])}")
        print(f"  预览: {r['content_preview'][:100]}...")
        print()

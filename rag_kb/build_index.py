#!/usr/bin/env python3
"""Build TF-IDF vector index for 科武纪元 science materials RAG."""
import json, math, re
from collections import Counter
from pathlib import Path

BASE = Path("/workspace/科武纪元")
CARDS = BASE / "rag_kb" / "science" / "cards" / "science_cards.jsonl"
INDEX_DIR = BASE / "rag_kb" / "science" / "index"

# ========== Load cards ==========
cards = []
with open(CARDS) as f:
    for line in f:
        cards.append(json.loads(line.strip()))

trusted = [c for c in cards if c["trust"] in ("A", "B")]
print(f"Building index for {len(trusted)} trusted cards")

# ========== Tokenizer ==========
def tokenize(text):
    tokens = []
    chinese = re.findall(r'[\u4e00-\u9fff]+', text)
    for seg in chinese:
        for i in range(len(seg) - 1):
            tokens.append(seg[i:i+2])
    for seg in chinese:
        if len(seg) >= 3:
            tokens.append(seg[:3])
        if len(seg) >= 4:
            tokens.append(seg[:4])
    eng = re.findall(r'[a-zA-Z]{3,}', text.lower())
    tokens.extend(eng)
    nums = re.findall(r'\d+\.?\d*[万亿千百]?[度瓦伏特焦]?[时秒年]?', text)
    tokens.extend(nums)
    return tokens

# ========== Build document frequency ==========
doc_freq = Counter()
doc_tokens = []
for c in trusted:
    text = f"{c['title']} {' '.join(c.get('domains', []))} {c.get('content', '')[:1000]}"
    toks = tokenize(text)
    doc_tokens.append(toks)
    for t in set(toks):
        doc_freq[t] += 1

N = len(trusted)

# Vocabulary: filter rare and ultra-common
vocab = {t: i for i, t in enumerate(
    t for t, df in doc_freq.items()
    if 1 <= df <= N * 0.8 and len(t) >= 2
)}
vocab_size = len(vocab)
print(f"Vocabulary size: {vocab_size}")

# ========== TF-IDF vectors ==========
import numpy as np

vectors = np.zeros((N, vocab_size), dtype=np.float32)
for i, toks in enumerate(doc_tokens):
    tf = Counter(toks)
    for t, count in tf.items():
        if t in vocab:
            j = vocab[t]
            vectors[i][j] = (1 + math.log(count)) * math.log(N / doc_freq[t])

norms = np.linalg.norm(vectors, axis=1, keepdims=True)
norms[norms == 0] = 1
vectors_norm = vectors / norms

# ========== Save ==========
INDEX_DIR.mkdir(parents=True, exist_ok=True)
np.save(INDEX_DIR / "tfidf_vectors.npy", vectors_norm)

meta = {
    "vocab_size": vocab_size,
    "num_docs": N,
    "doc_ids": [c["id"] for c in trusted],
    "doc_titles": [c["title"][:80] for c in trusted],
    "doc_sources": [c["source"] for c in trusted],
    "doc_domains": [c.get("domains", []) for c in trusted],
    "doc_trust": [c["trust"] for c in trusted],
}
with open(INDEX_DIR / "index_meta.json", "w", encoding="utf-8") as f:
    json.dump(meta, f, ensure_ascii=False, indent=2)

full_vocab = {t: int(i) for t, i in vocab.items()}
with open(INDEX_DIR / "vocab.json", "w", encoding="utf-8") as f:
    json.dump(full_vocab, f, ensure_ascii=False)

# ========== Search function ==========
def search(query, top_k=5):
    q_toks = tokenize(query)
    q_vec = np.zeros(vocab_size, dtype=np.float32)
    tf = Counter(q_toks)
    for t, count in tf.items():
        if t in vocab:
            j = vocab[t]
            q_vec[j] = (1 + math.log(count)) * math.log(N / doc_freq[t])
    norm = np.linalg.norm(q_vec)
    if norm > 0:
        q_vec /= norm
    scores = vectors_norm @ q_vec
    top_idx = np.argsort(scores)[::-1][:top_k]
    results = []
    for idx in top_idx:
        if scores[idx] > 0.01:
            results.append({
                "id": trusted[idx]["id"],
                "title": trusted[idx]["title"][:70],
                "source": trusted[idx]["source"],
                "trust": trusted[idx]["trust"],
                "score": round(float(scores[idx]), 4),
                "domains": trusted[idx].get("domains", [])[:3]
            })
    return results

# ========== Test queries ==========
queries = [
    "量子计算 纠错",
    "核聚变 人造太阳",
    "芯片 存算一体",
    "外骨骼 人工肌肉",
    "光学超材料 隐身",
    "FAST 天眼 信号",
    "供应链 制造",
    "基因 育种 SNP",
    "数据中心 耗水 散热",
]

print("\n========== 检索测试 ==========")
for q in queries:
    results = search(q, top_k=3)
    print(f"\n查询: {q}")
    for r in results:
        print(f"  [{r['trust']}] {r['score']:.3f} | {r['title']} ({r['source']}) [{','.join(r['domains'])}]")

print(f"\n========== 索引构建完成 ==========")
print(f"  向量矩阵: tfidf_vectors.npy {vectors_norm.shape}")
print(f"  词表: vocab.json ({len(full_vocab)} terms)")
print(f"  元数据: index_meta.json ({N} docs)")

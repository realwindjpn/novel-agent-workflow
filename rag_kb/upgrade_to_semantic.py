#!/usr/bin/env python3
"""Upgrade RAG index: TF-IDF -> SiliconFlow bge-m3 semantic vectors."""
import json, requests, time, hashlib
from pathlib import Path

API_KEY = "sk-jkeqvsnbvmygwffkrdtufsagshgfdaypklfjovfopnbzjwsw"
EMBED_URL = "https://api.siliconflow.cn/v1/embeddings"
MODEL = "BAAI/bge-m3"

CARDS_PATH = Path("/workspace/科武纪元/rag_kb/science/cards/science_cards.jsonl")
INDEX_DIR = Path("/workspace/科武纪元/rag_kb/science/index")

# Load cards
cards = []
with open(CARDS_PATH) as f:
    for line in f:
        cards.append(json.loads(line.strip()))

trusted = [c for c in cards if c["trust"] in ("A", "B")]
print(f"Embedding {len(trusted)} trusted cards with {MODEL}...")

# Build document texts for embedding (title + domains + first 500 chars)
doc_texts = []
for c in trusted:
    domains_str = " ".join(c.get("domains", []))
    content_preview = c.get("content", "")[:500]
    text = f"{c['title']} {domains_str} {content_preview}"
    doc_texts.append(text)

# Batch embed (SiliconFlow supports up to ~50 per request)
def embed_batch(texts):
    resp = requests.post(EMBED_URL,
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={"model": MODEL, "input": texts})
    data = resp.json()
    if 'data' in data:
        return [d['embedding'] for d in data['data']]
    else:
        raise Exception(f"Embedding failed: {data}")

# Embed in batches
all_embeddings = []
BATCH_SIZE = 20
for i in range(0, len(doc_texts), BATCH_SIZE):
    batch = doc_texts[i:i+BATCH_SIZE]
    print(f"  Batch {i//BATCH_SIZE + 1} ({len(batch)} texts)...")
    embs = embed_batch(batch)
    all_embeddings.extend(embs)
    if i + BATCH_SIZE < len(doc_texts):
        time.sleep(0.5)  # rate limit

print(f"Got {len(all_embeddings)} embeddings, dim={len(all_embeddings[0])}")

# Save vectors as numpy
import numpy as np
vectors = np.array(all_embeddings, dtype=np.float32)

# L2 normalize
norms = np.linalg.norm(vectors, axis=1, keepdims=True)
norms[norms == 0] = 1
vectors_norm = vectors / norms

# Save
np.save(INDEX_DIR / "semantic_vectors.npy", vectors_norm)

# Save metadata
meta = {
    "model": MODEL,
    "provider": "siliconflow",
    "dim": len(all_embeddings[0]),
    "num_docs": len(trusted),
    "doc_ids": [c["id"] for c in trusted],
    "doc_titles": [c["title"][:80] for c in trusted],
    "doc_sources": [c["source"] for c in trusted],
    "doc_domains": [c.get("domains", []) for c in trusted],
    "doc_trust": [c["trust"] for c in trusted],
}
with open(INDEX_DIR / "semantic_meta.json", "w", encoding="utf-8") as f:
    json.dump(meta, f, ensure_ascii=False, indent=2)

print(f"\nSaved semantic_vectors.npy {vectors_norm.shape}")
print(f"Saved semantic_meta.json")

# ========== Test semantic search ==========
def search_semantic(query, top_k=5):
    q_emb = embed_batch([query])[0]
    q_vec = np.array(q_emb, dtype=np.float32)
    norm = np.linalg.norm(q_vec)
    if norm > 0:
        q_vec /= norm
    scores = vectors_norm @ q_vec
    top_idx = np.argsort(scores)[::-1][:top_k]
    results = []
    for idx in top_idx:
        results.append({
            "id": trusted[idx]["id"],
            "trust": trusted[idx]["trust"],
            "source": trusted[idx]["source"],
            "title": trusted[idx]["title"][:70],
            "domains": trusted[idx].get("domains", [])[:3],
            "score": round(float(scores[idx]), 4),
            "content_preview": trusted[idx].get("content", "")[:200],
        })
    return results

# Test queries
queries = [
    "外骨骼 仿生肌肉 本体感觉",
    "量子计算 纠错 祖冲之",
    "核聚变 人造太阳 能源",
    "芯片 存算一体 本地推理",
    "光学超材料 隐身 伪装",
    "供应链 印度 富士康",
    "数据中心 散热 耗水 AI",
    "基因检测 分子识别 生物芯片",
]

print("\n========== 语义检索测试 ==========")
for q in queries:
    results = search_semantic(q, top_k=3)
    print(f"\n查询: {q}")
    for r in results:
        print(f"  [{r['trust']}] {r['score']:.4f} | {r['title']}")
        print(f"    {r['source']} [{','.join(r['domains'])}]")

print("\n========== 向量索引升级完成 ==========")

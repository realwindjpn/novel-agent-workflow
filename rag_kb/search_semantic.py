#!/usr/bin/env python3
"""科武纪元 RAG 语义检索工具
使用 SiliconFlow bge-m3 向量索引，支持语义相似度搜索。
用法: python3 search_semantic.py "查询关键词" [top_k]
"""
import json, requests, sys, time
from pathlib import Path
import numpy as np

API_KEY = "sk-jkeqvsnbvmygwffkrdtufsagshgfdaypklfjovfopnbzjwsw"
EMBED_URL = "https://api.siliconflow.cn/v1/embeddings"
MODEL = "BAAI/bge-m3"

INDEX_DIR = Path("/workspace/科武纪元/rag_kb/science/index")
CARDS_PATH = Path("/workspace/科武纪元/rag_kb/science/cards/science_cards.jsonl")

# Load semantic vectors
vectors_norm = np.load(INDEX_DIR / "semantic_vectors.npy")
with open(INDEX_DIR / "semantic_meta.json", encoding="utf-8") as f:
    meta = json.load(f)

# Load full card content
cards = {}
with open(CARDS_PATH) as f:
    for line in f:
        c = json.loads(line.strip())
        cards[c["id"]] = c

N = meta["num_docs"]

def embed(text):
    resp = requests.post(EMBED_URL,
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={"model": MODEL, "input": [text]})
    data = resp.json()
    if 'data' in data:
        emb = data['data'][0]['embedding']
        v = np.array(emb, dtype=np.float32)
        norm = np.linalg.norm(v)
        if norm > 0:
            v /= norm
        return v
    else:
        raise Exception(f"Embedding failed: {data}")

def search(query, top_k=5):
    """语义检索，返回 top_k 最相关素材"""
    q_vec = embed(query)
    scores = vectors_norm @ q_vec
    top_idx = np.argsort(scores)[::-1][:top_k]
    results = []
    for idx in top_idx:
        if scores[idx] > 0.1:
            card_id = meta["doc_ids"][idx]
            card = cards.get(card_id, {})
            results.append({
                "id": card_id,
                "trust": meta["doc_trust"][idx],
                "source": meta["doc_sources"][idx],
                "title": meta["doc_titles"][idx],
                "domains": meta["doc_domains"][idx][:3],
                "score": round(float(scores[idx]), 4),
                "content_preview": card.get("content", "")[:400],
                "url": card.get("url", ""),
            })
    return results

def format_result(r):
    """格式化单条结果"""
    lines = []
    trust_tag = f"[{r['trust']}]"
    lines.append(f"{trust_tag} 相关度 {r['score']:.3f} | {r['title']}")
    lines.append(f"  来源: {r['source']} | 领域: {','.join(r['domains'])}")
    preview = r['content_preview'][:200].replace('\n', ' ')
    lines.append(f"  预览: {preview}...")
    if r.get('url'):
        lines.append(f"  链接: {r['url']}")
    return '\n'.join(lines)

if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "量子计算"
    top_k = 5
    if len(sys.argv) > 2 and sys.argv[2].isdigit():
        top_k = int(sys.argv[2])
    
    results = search(query, top_k=top_k)
    print(f"🔍 查询: {query}")
    print(f"📊 命中: {len(results)} 条 | 模型: {MODEL}\n")
    for r in results:
        print(format_result(r))
        print()

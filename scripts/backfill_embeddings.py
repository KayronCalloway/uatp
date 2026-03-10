#!/usr/bin/env python3
"""
Backfill embeddings for capsules (SQLite compatible).
"""
import hashlib
import json
import logging
import math
import os
import re
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timezone
from typing import List, Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

MODEL_NAME = "tfidf-v1"
EMBEDDING_DIM = 512

def tokenize(text: str) -> List[str]:
    text = text.lower()
    return re.findall(r'\b[a-z][a-z0-9]{2,}\b', text)

def hash_token(token: str, dim: int = EMBEDDING_DIM) -> int:
    h = hashlib.md5(token.encode()).hexdigest()
    return int(h, 16) % dim

def compute_tf(tokens: List[str]) -> Dict[str, float]:
    counts = Counter(tokens)
    total = len(tokens) if tokens else 1
    return {token: count / total for token, count in counts.items()}

def compute_tfidf_vector(text: str, idf_cache: Dict[str, float]) -> List[float]:
    tokens = tokenize(text)
    if not tokens:
        return [0.0] * EMBEDDING_DIM
    
    tf = compute_tf(tokens)
    vector = [0.0] * EMBEDDING_DIM
    
    for token, tf_val in tf.items():
        idf = idf_cache.get(token, 1.0)
        tfidf = tf_val * idf
        idx = hash_token(token)
        sign = 1 if int(hashlib.md5((token + "_sign").encode()).hexdigest(), 16) % 2 == 0 else -1
        vector[idx] += sign * tfidf
    
    # L2 normalize
    norm = math.sqrt(sum(v * v for v in vector))
    if norm > 0:
        vector = [v / norm for v in vector]
    
    return vector

def extract_text(capsule: Dict[str, Any]) -> str:
    parts = []
    payload = capsule.get("payload", {})
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except:
            payload = {}
    
    if prompt := payload.get("prompt"):
        parts.append(f"Task: {prompt}")
    
    for step in payload.get("reasoning_steps", [])[:10]:
        if isinstance(step, dict) and (r := step.get("reasoning")):
            parts.append(r[:500])
    
    if not parts:
        if capsule_type := capsule.get("capsule_type"):
            parts.append(capsule_type)
    
    return " ".join(parts)[:8000] or "empty capsule"

def backfill_embeddings(db_path: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Get capsules without embeddings
    cur.execute("""
        SELECT capsule_id, capsule_type, payload 
        FROM capsules 
        WHERE embedding IS NULL
        ORDER BY timestamp DESC
    """)
    rows = cur.fetchall()
    
    if not rows:
        print("No capsules need embedding")
        return
    
    print(f"Backfilling {len(rows)} capsules...")
    
    # Extract all texts
    all_data = []
    for row in rows:
        capsule = dict(row)
        text = extract_text(capsule)
        all_data.append((capsule['capsule_id'], text))
    
    # Build IDF
    doc_freq = Counter()
    for _, text in all_data:
        for token in set(tokenize(text)):
            doc_freq[token] += 1
    
    doc_count = len(all_data)
    idf_cache = {
        token: math.log((doc_count + 1) / (df + 1)) + 1 
        for token, df in doc_freq.items()
    }
    print(f"Built IDF from {doc_count} docs, {len(idf_cache)} terms")
    
    # Generate and save embeddings
    for i, (capsule_id, text) in enumerate(all_data):
        embedding = compute_tfidf_vector(text, idf_cache)
        cur.execute("""
            UPDATE capsules 
            SET embedding = ?, embedding_model = ?, embedding_created_at = ?
            WHERE capsule_id = ?
        """, (json.dumps(embedding), MODEL_NAME, datetime.now(timezone.utc).isoformat(), capsule_id))
        
        if (i + 1) % 20 == 0:
            conn.commit()
            print(f"Processed {i + 1}/{len(all_data)}")
    
    conn.commit()
    conn.close()
    print(f"Done! Embedded {len(all_data)} capsules")

if __name__ == "__main__":
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uatp_dev.db")
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    backfill_embeddings(db_path)

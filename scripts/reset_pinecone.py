import sys
import os
sys.path.append(os.path.abspath("."))

from pinecone import Pinecone
from app.config import PINECONE_API_KEY, PINECONE_INDEX

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX)

stats = index.describe_index_stats()
namespaces = stats.get("namespaces", {}).keys()

for ns in namespaces:
    print(f"🧨 Deleting namespace: '{ns}'")
    index.delete(delete_all=True, namespace=ns)

print("✅ ALL namespaces wiped clean")

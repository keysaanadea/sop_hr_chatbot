import sys
import os
sys.path.append(os.path.abspath("."))

from pinecone import Pinecone
from app.config import PINECONE_API_KEY, PINECONE_INDEX

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX)

stats = index.describe_index_stats()
print("📊 INDEX STATS:")
print(stats)

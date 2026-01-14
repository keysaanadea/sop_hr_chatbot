# scripts/run_ingest.py
import sys
import os

sys.path.append(os.path.abspath("."))

from ingestion.ingest_pdf import main

if __name__ == "__main__":
    print("🚀 STARTING SOP INGESTION")
    print("📂 Source: documents/")
    print("📌 Target: Pinecone Index")
    print("-" * 40)

    main()

    print("-" * 40)
    print("🎉 INGESTION FINISHED")

#!/usr/bin/env python3
"""
scripts/index_rag.py — One-time script to index the Andromeda refund policy into ChromaDB.

Run this before enabling RAG_ENABLED=true:
    python scripts/index_rag.py
    python scripts/index_rag.py --force  # rebuild index from scratch
    python scripts/index_rag.py --check  # only print stats, no indexing
"""

import argparse
import sys
from pathlib import Path

# Make backend importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))


def main():
    parser = argparse.ArgumentParser(description="Index Andromeda policy into ChromaDB")
    parser.add_argument("--force", action="store_true", help="Rebuild index from scratch")
    parser.add_argument("--check", action="store_true", help="Print stats only, no indexing")
    args = parser.parse_args()

    from app.rag.retriever import _get_collection, index_policy

    collection = _get_collection()

    if args.check:
        count = collection.count()
        print(f"\nChromaDB collection 'andromeda_refund_policy'")
        print(f"  Chunks indexed: {count}")
        print(f"  Status: {'✅ Ready' if count > 0 else '⚠️  Empty — run without --check to index'}\n")
        return

    print("\nIndexing Andromeda refund policy into ChromaDB...")
    count = index_policy(force=args.force)
    print(f"✅ Indexed {count} policy chunks")

    # Quick retrieval test
    from app.rag.retriever import retrieve_relevant_policy
    test_query = "return window expired jacket"
    chunks = retrieve_relevant_policy(test_query)
    print(f"\nRetrieval test: '{test_query}'")
    for i, chunk in enumerate(chunks, 1):
        print(f"  [{i}] section='{chunk['section']}' score={chunk['score']:.3f}")
    print()


if __name__ == "__main__":
    main()

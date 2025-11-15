#!/usr/bin/env python3
"""
build_classes.py (Weaviate Server 1.34.0 + weaviate-client 4.17.0)
-----------------------------------------------------------------
This script rebuilds the schema using the **new v4 Collections API**.
The old `client.schema.*` interface is deprecated in v4.

This version is **fully compatible** with:
- Weaviate Server **1.34.0**
- weaviate-client **4.17.0**

It does the following:
1. Connects to the running Weaviate instance
2. Deletes ALL existing collections
3. Reads a JSON schema file
4. Creates collections using the v4 API

Usage:
    python build_classes.py weaviate_schema.json

If no file is provided, defaults to "weaviate_schema.json".
"""

import json
import sys
import weaviate
from weaviate.classes.config import Property, DataType, Configure


def main() -> None:
    # ------------------------------------------------------------------
    # Determine schema file path
    # ------------------------------------------------------------------
    schema_path = sys.argv[1] if len(sys.argv) > 1 else "weaviate_schema.json"
    print(f"[INFO] Using schema file: {schema_path}")

    # ------------------------------------------------------------------
    # Connect to local Weaviate server
    # ------------------------------------------------------------------
    print("[INFO] Connecting to local Weaviate instance at http://localhost:8080 ...")
    client = weaviate.connect_to_local()

    print("[INFO] Checking Weaviate readiness...")
    if not client.is_ready():
        print("[ERROR] Weaviate is not ready. Is Docker running?")
        raise SystemExit(1)
    print("[INFO] Weaviate is ready.")

    # ------------------------------------------------------------------
    # Load schema JSON
    # ------------------------------------------------------------------
    print(f"[INFO] Loading schema JSON from: {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    classes = schema.get("classes", [])
    print(f"[INFO] JSON schema contains {len(classes)} classes.")

    # ------------------------------------------------------------------
    # Delete ALL existing collections
    # ------------------------------------------------------------------
    print("[INFO] Deleting ALL existing collections...")
    for c in client.collections.list_all():
        print(f"  → Deleting collection: {c}")
        client.collections.delete(c)
    print("[INFO] All collections deleted.")

    # ------------------------------------------------------------------
    # Create new collections using v4 Collections API
    # ------------------------------------------------------------------
    print("[INFO] Creating new collections...")
    for cls in classes:
        class_name = cls.get("name")
        print(f"  → Creating: {class_name}")

        # Vectorizer
        vectorizer = cls.get("vectorizer", "none")
        if vectorizer == "text2vec-openai":
            vectorizer_cfg = Configure.Vectorizer.text2vec_openai()
        else:
            vectorizer_cfg = Configure.Vectorizer.none()

        # Properties
        props = []
        for p in cls.get("properties", []):
            name = p["name"]
            dtype = p["data_type"][0]

            dtype_map = {
                "text": DataType.TEXT,
                "text[]": DataType.TEXT_ARRAY,
                "number": DataType.NUMBER,
                "int": DataType.INT,
                "boolean": DataType.BOOL,
            }

            props.append(Property(name=name, data_type=dtype_map[dtype]))

        client.collections.create(
            name=class_name,
            properties=props,
            vectorizer_config=vectorizer_cfg,
        )

    print("[INFO] Schema rebuild complete.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3

"""
weaviate_store.py
-----------------
This module provides a `WeaviateStore` class for managing a Weaviate vector database instance.

Weaviate is an open-source vector database that allows you to store, index, and search data using both traditional and vector-based (semantic) queries. It is commonly used for applications involving large-scale semantic search, LLM retrieval, and AI-powered data pipelines.

This class demonstrates how to:
    1. Connect to a running Weaviate instance using the v4 client API
    2. Load schema configuration from a JSON file (path set in .env)
    3. Delete all existing collections (classes) in Weaviate
    4. Create new collections based on the loaded schema

Key Concepts:
    - A "collection" (previously called "class") is a table-like structure in Weaviate for storing objects of a certain type.
    - Each collection has properties (fields) and a vectorizer (how objects are embedded for vector search).
    - The v4 API uses `client.collections` for all schema and data operations (not `client.schema`).

Example usage:
    from store.weaviate_store import WeaviateStore
    ws = WeaviateStore()
    ws.rebuild_schema()  # DANGER: This will delete all collections and recreate them from schema

Environment variables (see .env):
    WEAVIATE_URL, WEAVIATE_GRPC_PORT, WEAVIATE_SCHEMA_PATH
"""


import json
import os
import weaviate
from weaviate.classes.config import Property, DataType, Configure
from config import settings
from utils.logger import AppLogger



class WeaviateStore:
    """
    A utility class for interacting with an existing Weaviate instance.
    Provides methods to insert CV and JobDescription objects into their respective collections.
    Logs all actions using AppLogger.
    """

    def __init__(self, url=None, grpc_port=None, log_file_path=None):
        """
        Initialize the WeaviateStore.
        Loads config from .env via config.settings and connects to Weaviate.
        Sets up the logger using the log file path from settings.py.
        """
        self.url = url or os.getenv("WEAVIATE_URL", "http://localhost:8080")
        self.grpc_port = grpc_port or int(os.getenv("WEAVIATE_GRPC_PORT", "50051"))
        self.client = weaviate.Client(
            url=self.url,
            grpc_port=self.grpc_port,
        )
        # Get log file path from settings.py (which loads .env)
        log_path = log_file_path
        if not log_path:
            log_path = os.getenv("LOG_FILE_PATH")
        if not log_path:
            # fallback if not set
            log_path = "logs/app.log"
        self.logger = AppLogger(log_path)

    def create_cv_object(self, cv_json_path: str) -> str:
        """
        Insert a CV object into the 'CV' collection from a JSON file.
        Logs the action and prints the returned UUID.
        Args:
            cv_json_path (str): Path to the CV JSON file.
        Returns:
            str: The UUID of the created object.
        """
        if not os.path.isfile(cv_json_path):
            self.logger.log(f"CV JSON file not found: {cv_json_path}")
            raise FileNotFoundError(f"CV JSON file not found: {cv_json_path}")
        with open(cv_json_path, "r", encoding="utf-8") as f:
            obj = json.load(f)
        self.logger.log(f"Inserting CV object from {cv_json_path} into 'CV' collection.")
        uuid = self.client.collections.get("CV").data.insert(obj)
        self.logger.log_kv("CV_OBJECT_CREATED", uuid=uuid, file=cv_json_path)
        print(f"[CV] Inserted object UUID: {uuid}")
        return uuid

    def create_jd_object(self, jd_json_path: str) -> str:
        """
        Insert a JobDescription object into the 'JobDescription' collection from a JSON file.
        Logs the action and prints the returned UUID.
        Args:
            jd_json_path (str): Path to the JobDescription JSON file.
        Returns:
            str: The UUID of the created object.
        """
        if not os.path.isfile(jd_json_path):
            self.logger.log(f"JobDescription JSON file not found: {jd_json_path}")
            raise FileNotFoundError(f"JobDescription JSON file not found: {jd_json_path}")
        with open(jd_json_path, "r", encoding="utf-8") as f:
            obj = json.load(f)
        self.logger.log(f"Inserting JobDescription object from {jd_json_path} into 'JobDescription' collection.")
        uuid = self.client.collections.get("JobDescription").data.insert(obj)
        self.logger.log_kv("JD_OBJECT_CREATED", uuid=uuid, file=jd_json_path)
        print(f"[JobDescription] Inserted object UUID: {uuid}")
        return uuid

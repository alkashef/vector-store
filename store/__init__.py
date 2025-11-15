"""Store package: Weaviate plumbing and facades.

Exports:
- WeaviateStore: central client + schema plumbing

Notes
- Legacy facades (CVStore, RoleStore) are not used in this project version
	and have been removed to avoid import errors.
"""
from .weaviate_store import WeaviateStore  # noqa: F401

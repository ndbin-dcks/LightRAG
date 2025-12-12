"""
HiRAG Hierarchical Extension for LightRAG

This package adds hierarchical community detection and multi-layer querying
to LightRAG without modifying the core codebase.

Features:
- Multi-layer entity clustering (Layer 1, 2, 3...)
- LLM-powered community summarization
- Hierarchical query modes
- PostgreSQL storage integration

Usage:
    from lightrag import LightRAG, QueryParam
    
    # Enable hierarchical mode
    rag = LightRAG(
        working_dir="./rag_storage",
        enable_hierarchical=True
    )
    
    # Build hierarchy
    await rag.hierarchical_ext.build_full_hierarchy()
    
    # Query
    result = await rag.aquery(
        "Your question?",
        param=QueryParam(mode="hierarchical")
    )
"""

from .extension import HierarchicalExtension
from .clustering import GMM_cluster, get_optimal_clusters
from .query import hierarchical_query

__all__ = [
    'HierarchicalExtension',
    'GMM_cluster',
    'get_optimal_clusters',
    'hierarchical_query',
]

__version__ = '1.0.0'

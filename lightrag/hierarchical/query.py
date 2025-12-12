"""
Query functions for hierarchical retrieval

This module implements multi-layer vector search and context building
for hierarchical query modes.
"""

import json
import logging
import numpy as np
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


async def vector_search_layer(
    query: str,
    layer: int,
    db,
    workspace: str,
    embed_func,
    top_k: int = 10
) -> List[Dict[str, Any]]:
    """
    Vector search in specific layer
    
    Args:
        query: Query string
        layer: Layer number (0=entities, 1+=communities)
        db: Database connection
        workspace: Workspace identifier
        embed_func: Embedding function
        top_k: Number of results to return
        
    Returns:
        List of search results with content and distance
    """
    try:
        # Get query embedding
        query_embeddings = await embed_func([query])
        query_embedding = query_embeddings[0] if isinstance(query_embeddings[0], list) else query_embeddings[0].tolist()
        query_vec = json.dumps(query_embedding)
        
        if layer == 0:
            # Search Layer 0 entities
            sql = """
                SELECT id, entity_name, description as content,
                       content_vector <=> $1::vector AS distance
                FROM lightrag_vdb_entity
                WHERE workspace = $2
                ORDER BY distance
                LIMIT $3
            """
            results = await db.fetch(sql, query_vec, workspace, top_k)
            
            return [
                {
                    'id': r['id'],
                    'name': r['entity_name'],
                    'content': r['content'],
                    'distance': float(r['distance']),
                    'layer': 0
                }
                for r in results
            ]
        
        else:
            # Search communities
            sql = """
                SELECT id, title, summary, report_json,
                       embedding <=> $1::vector AS distance
                FROM lightrag_communities
                WHERE workspace = $2 AND layer = $3
                ORDER BY distance
                LIMIT $4
            """
            results = await db.fetch(sql, query_vec, workspace, layer, top_k)
            
            return [
                {
                    'id': r['id'],
                    'title': r['title'],
                    'summary': r['summary'],
                    'report_json': json.loads(r['report_json']) if r['report_json'] else {},
                    'distance': float(r['distance']),
                    'layer': layer
                }
                for r in results
            ]
            
    except Exception as e:
        logger.error(f"Vector search failed for layer {layer}: {e}")
        return []


def build_hierarchical_context(
    layer_0_results: List[Dict[str, Any]],
    layer_1_results: List[Dict[str, Any]],
    layer_2_results: List[Dict[str, Any]] = None
) -> str:
    """
    Build hierarchical context from multi-layer search results
    
    Combines results from different layers into a structured context
    with highest abstraction first (top-down presentation).
    
    Args:
        layer_0_results: Entity-level results
        layer_1_results: Community-level results
        layer_2_results: Chapter-level results (optional)
        
    Returns:
        Formatted context string
    """
    context_parts = []
    
    # Layer 2 (highest abstraction) - if available
    if layer_2_results:
        context_parts.append("# CẤP ĐỘ TỔNG QUAN (Chapter-level)\n")
        for i, item in enumerate(layer_2_results, 1):
            context_parts.append(f"## {i}. {item['title']}")
            context_parts.append(f"{item['summary']}\n")
            
            # Add findings if available
            if item.get('report_json') and item['report_json'].get('findings'):
                context_parts.append("**Các điểm chính:**")
                for finding in item['report_json']['findings']:
                    context_parts.append(f"- {finding.get('summary', '')}: {finding.get('explanation', '')}")
                context_parts.append("")
    
    # Layer 1 (community level)
    if layer_1_results:
        context_parts.append("\n# CẤP ĐỘ CHI TIẾT (Community-level)\n")
        for i, item in enumerate(layer_1_results, 1):
            context_parts.append(f"## {i}. {item['title']}")
            context_parts.append(f"{item['summary']}\n")
            
            # Add findings if available
            if item.get('report_json') and item['report_json'].get('findings'):
                context_parts.append("**Thông tin chi tiết:**")
                for finding in item['report_json']['findings']:
                    context_parts.append(f"- {finding.get('summary', '')}: {finding.get('explanation', '')}")
                context_parts.append("")
    
    # Layer 0 (entity level)
    if layer_0_results:
        context_parts.append("\n# THỰC THỂ CỤ THỂ (Entity-level)\n")
        for i, item in enumerate(layer_0_results, 1):
            context_parts.append(f"{i}. **{item['name']}**: {item['content']}")
    
    return "\n".join(context_parts)


async def hierarchical_query(
    query: str,
    lightrag_instance,
    hierarchical_ext,
    param
) -> str:
    """
    Query across all hierarchical layers
    
    This is the main query function for hierarchical mode.
    It searches across Layer 0, 1, 2 and synthesizes information.
    
    Args:
        query: User query
        lightrag_instance: LightRAG instance
        hierarchical_ext: HierarchicalExtension instance
        param: Query parameters
        
    Returns:
        Answer string
    """
    logger.info(f"Hierarchical query: {query}")
    
    db = hierarchical_ext.db
    workspace = hierarchical_ext.workspace
    embed_func = hierarchical_ext.embed_func
    llm_func = hierarchical_ext.llm_func
    
    # Step 1: Get statistics to know available layers
    stats = await hierarchical_ext.storage.get_statistics()
    available_layers = list(stats['layers'].keys())
    max_layer = max(available_layers) if available_layers else 0
    
    logger.info(f"Available layers: {available_layers} (max: {max_layer})")
    
    # Step 2: Vector search in all layers
    layer_0_results = await vector_search_layer(
        query, 0, db, workspace, embed_func, top_k=20
    )
    logger.info(f"Layer 0 results: {len(layer_0_results)}")
    
    layer_1_results = []
    if 1 in available_layers:
        layer_1_results = await vector_search_layer(
            query, 1, db, workspace, embed_func, top_k=5
        )
        logger.info(f"Layer 1 results: {len(layer_1_results)}")
    
    layer_2_results = []
    if 2 in available_layers:
        layer_2_results = await vector_search_layer(
            query, 2, db, workspace, embed_func, top_k=2
        )
        logger.info(f"Layer 2 results: {len(layer_2_results)}")
    
    # Step 3: Build hierarchical context
    context = build_hierarchical_context(
        layer_0_results,
        layer_1_results,
        layer_2_results if layer_2_results else None
    )
    
    # Step 4: Generate answer with LLM
    prompt = f"""Bạn là trợ lý AI chuyên về luật pháp Việt Nam, đặc biệt là Luật Địa chất và Khoáng sản.

Dưới đây là thông tin từ cơ sở tri thức được tổ chức theo cấu trúc phân cấp (từ tổng quan đến chi tiết):

{context}

Câu hỏi của người dùng: {query}

Hãy trả lời câu hỏi dựa trên thông tin được cung cấp ở cả ba cấp độ:
1. Sử dụng thông tin tổng quan (nếu có) để đưa ra bức tranh toàn cảnh
2. Dùng thông tin chi tiết từ các community để làm rõ các khía cạnh cụ thể
3. Trích dẫn các thực thể (entities) để hỗ trợ câu trả lời với thông tin chính xác

Yêu cầu:
- Trả lời đầy đủ, chính xác dựa trên ngữ cảnh
- Cấu trúc rõ ràng, dễ hiểu
- Trích dẫn cụ thể các điều luật/thực thể liên quan
- Nếu thông tin không đủ để trả lời, hãy nói rõ phần nào thiếu

Trả lời:"""
    
    try:
        answer = await llm_func(prompt, max_tokens=param.response_type if hasattr(param, 'response_type') else 2000)
        logger.info("Answer generated successfully")
        return answer
    except Exception as e:
        logger.error(f"Failed to generate answer: {e}")
        return f"Xin lỗi, đã xảy ra lỗi khi tạo câu trả lời: {str(e)}"


async def hierarchical_local_query(
    query: str,
    lightrag_instance,
    hierarchical_ext,
    param
) -> str:
    """
    Query focused on Layer 0 entities and relationships
    
    Similar to LightRAG's local mode but uses hierarchical structure.
    
    Args:
        query: User query
        lightrag_instance: LightRAG instance
        hierarchical_ext: HierarchicalExtension instance
        param: Query parameters
        
    Returns:
        Answer string
    """
    logger.info(f"Hierarchical local query: {query}")
    
    # Search only Layer 0
    layer_0_results = await vector_search_layer(
        query, 0, 
        hierarchical_ext.db, 
        hierarchical_ext.workspace, 
        hierarchical_ext.embed_func, 
        top_k=30
    )
    
    # Build context from entities only
    context_parts = ["# THÔNG TIN CHI TIẾT\n"]
    for i, item in enumerate(layer_0_results, 1):
        context_parts.append(f"{i}. **{item['name']}**: {item['content']}")
    
    context = "\n".join(context_parts)
    
    # Generate answer
    prompt = f"""Dựa trên thông tin chi tiết sau:

{context}

Câu hỏi: {query}

Hãy trả lời dựa trên các thực thể cụ thể được cung cấp:"""
    
    answer = await hierarchical_ext.llm_func(prompt)
    return answer


async def hierarchical_global_query(
    query: str,
    lightrag_instance,
    hierarchical_ext,
    param
) -> str:
    """
    Query focused on high-level communities (Layer 1, 2)
    
    Similar to LightRAG's global mode but uses hierarchical communities.
    
    Args:
        query: User query
        lightrag_instance: LightRAG instance
        hierarchical_ext: HierarchicalExtension instance
        param: Query parameters
        
    Returns:
        Answer string
    """
    logger.info(f"Hierarchical global query: {query}")
    
    # Search Layer 1 and Layer 2
    layer_1_results = await vector_search_layer(
        query, 1,
        hierarchical_ext.db,
        hierarchical_ext.workspace,
        hierarchical_ext.embed_func,
        top_k=10
    )
    
    layer_2_results = await vector_search_layer(
        query, 2,
        hierarchical_ext.db,
        hierarchical_ext.workspace,
        hierarchical_ext.embed_func,
        top_k=5
    )
    
    # Build context from communities only
    context = build_hierarchical_context([], layer_1_results, layer_2_results)
    
    # Generate answer
    prompt = f"""Dựa trên thông tin tổng quan và chi tiết sau:

{context}

Câu hỏi: {query}

Hãy trả lời dựa trên các báo cáo community được cung cấp:"""
    
    answer = await hierarchical_ext.llm_func(prompt)
    return answer


async def get_entity_communities(
    entity_id: str,
    hierarchical_ext
) -> List[Dict[str, Any]]:
    """
    Get all communities that contain a specific entity
    
    Useful for understanding the hierarchical context of an entity.
    
    Args:
        entity_id: Entity ID
        hierarchical_ext: HierarchicalExtension instance
        
    Returns:
        List of communities containing this entity
    """
    try:
        sql = """
            SELECT c.id, c.layer, c.title, c.summary, cm.membership_score
            FROM lightrag_communities c
            JOIN lightrag_community_members cm ON c.id = cm.community_id
            WHERE cm.workspace = $1 AND cm.member_id = $2
            ORDER BY c.layer, cm.membership_score DESC
        """
        
        results = await hierarchical_ext.db.fetch(
            sql,
            hierarchical_ext.workspace,
            entity_id
        )
        
        return [dict(r) for r in results]
        
    except Exception as e:
        logger.error(f"Failed to get entity communities: {e}")
        return []


async def get_community_hierarchy(
    community_id: str,
    hierarchical_ext
) -> Dict[str, Any]:
    """
    Get parent and children of a community
    
    Args:
        community_id: Community ID
        hierarchical_ext: HierarchicalExtension instance
        
    Returns:
        Dict with 'parent' and 'children' keys
    """
    try:
        # Get parent
        sql_parent = """
            SELECT c.id, c.layer, c.title, c.summary
            FROM lightrag_communities c
            JOIN lightrag_community_hierarchy ch ON c.id = ch.parent_id
            WHERE ch.workspace = $1 AND ch.child_id = $2
        """
        parent = await hierarchical_ext.db.fetch_one(
            sql_parent,
            hierarchical_ext.workspace,
            community_id
        )
        
        # Get children
        sql_children = """
            SELECT c.id, c.layer, c.title, c.summary
            FROM lightrag_communities c
            JOIN lightrag_community_hierarchy ch ON c.id = ch.child_id
            WHERE ch.workspace = $1 AND ch.parent_id = $2
            ORDER BY c.title
        """
        children = await hierarchical_ext.db.fetch(
            sql_children,
            hierarchical_ext.workspace,
            community_id
        )
        
        return {
            'parent': dict(parent) if parent else None,
            'children': [dict(c) for c in children]
        }
        
    except Exception as e:
        logger.error(f"Failed to get community hierarchy: {e}")
        return {'parent': None, 'children': []}

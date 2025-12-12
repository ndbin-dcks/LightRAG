"""
Main HierarchicalExtension class - CORRECTED VERSION

This class extends LightRAG with hierarchical clustering capabilities
without modifying the original LightRAG code.

FIXES APPLIED:
1. ✅ Lazy-load database connection via @property
2. ✅ Correct LLM function attribute name (llm_model_func not best_model_func)
3. ✅ Lazy-load storage helper to ensure valid db connection
"""

import asyncio
import numpy as np
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from .clustering import (
    perform_clustering,
    calculate_cluster_sparsity,
    CLUSTERING_AVAILABLE
)
from .storage import CommunityStorage

logger = logging.getLogger(__name__)


class HierarchicalExtension:
    """
    Extension class for hierarchical community detection in LightRAG
    
    This class adds Layer 1, 2, 3... communities on top of Layer 0 entities
    without modifying the original LightRAG code.
    
    Features:
    - Automatic clustering with GMM + BIC
    - LLM-powered community summarization
    - Multi-layer hierarchical structure
    - PostgreSQL storage integration
    """
    
    def __init__(self, lightrag_instance):
        """
        Initialize extension
        
        Args:
            lightrag_instance: LightRAG instance to extend
        """
        if not CLUSTERING_AVAILABLE:
            raise RuntimeError(
                "Hierarchical extension requires umap-learn and scikit-learn. "
                "Install with: pip install umap-learn scikit-learn"
            )
        
        self.lightrag = lightrag_instance
        self.workspace = lightrag_instance.workspace
        
        # ✅ FIXED: Correct attribute name (was best_model_func)
        self.llm_func = lightrag_instance.llm_model_func
        self.embed_func = lightrag_instance.embedding_func
        
        # Configuration
        self.config = {
            'max_layers': 10,
            'reduction_dimension': 2,
            'cluster_threshold': 0.1,
            'max_clusters': 50,
            'sparsity_threshold': 0.98,
            'min_entities_per_layer': 2,
            'random_state': 42
        }
        
        logger.info(f"HierarchicalExtension initialized for workspace: {self.workspace}")
    
    # ✅ FIXED: Lazy-load database connection
    @property
    def db(self):
        """
        Lazy-load database connection
        
        This ensures db is only accessed AFTER initialize_storages() has been called
        on the parent LightRAG instance.
        
        Returns:
            Database connection from chunk_entity_relation_graph
        """
        return self.lightrag.chunk_entity_relation_graph.db
    
    # ✅ FIXED: Lazy-load storage helper
    @property
    def storage(self):
        """
        Lazy-load storage helper
        
        Creates CommunityStorage on-demand with current db connection.
        This ensures the storage helper always has a valid database connection.
        
        Returns:
            CommunityStorage instance
        """
        if not hasattr(self, '_storage') or self._storage is None:
            self._storage = CommunityStorage(self.db, self.workspace)
        return self._storage
    
    async def load_layer_0_entities(self) -> List[Dict[str, Any]]:
        """
        Load Layer 0 entities from PostgreSQL
        
        Returns:
            List of entity dicts with id, entity_name, description, embedding
        """
        try:
            sql = """
                SELECT id, entity_name, description, content_vector
                FROM lightrag_vdb_entity
                WHERE workspace = $1
                ORDER BY id
            """
            
            rows = await self.db.fetch(sql, self.workspace)
            
            entities = []
            for row in rows:
                entity = {
                    'id': row['id'],
                    'entity_name': row['entity_name'],
                    'description': row['description'],
                    'embedding': json.loads(row['content_vector']) if isinstance(row['content_vector'], str) else row['content_vector']
                }
                entities.append(entity)
            
            logger.info(f"Loaded {len(entities)} Layer 0 entities")
            return entities
            
        except Exception as e:
            logger.error(f"Failed to load Layer 0 entities: {e}")
            return []
    
    async def build_layer(
        self,
        input_entities: List[Dict[str, Any]],
        layer: int
    ) -> List[Dict[str, Any]]:
        """
        Build single hierarchical layer
        
        Process:
        1. Extract embeddings from input entities
        2. UMAP reduction + GMM clustering
        3. For each cluster: LLM summarization
        4. Create community entities
        
        Args:
            input_entities: Entities from previous layer
            layer: Current layer number (1, 2, 3...)
            
        Returns:
            List of community entities for this layer
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"Building Layer {layer} from {len(input_entities)} entities")
        logger.info(f"{'='*60}")
        
        if len(input_entities) < self.config['min_entities_per_layer']:
            logger.info(f"Too few entities ({len(input_entities)}). Stopping.")
            return []
        
        # Step 1: Prepare embeddings
        embeddings = np.array([e['embedding'] for e in input_entities])
        logger.info(f"[1/4] Embeddings prepared: {embeddings.shape}")
        
        # Step 2: Clustering
        logger.info(f"[2/4] Starting clustering...")
        labels, n_clusters, reduced_embeddings, probs = perform_clustering(
            embeddings,
            reduction_dimension=self.config['reduction_dimension'],
            cluster_threshold=self.config['cluster_threshold'],
            max_clusters=self.config['max_clusters'],
            random_state=self.config['random_state']
        )
        
        logger.info(f"[2/4] Clustering complete: {n_clusters} clusters")
        
        # Check sparsity
        sparsity = calculate_cluster_sparsity(labels, len(input_entities))
        logger.info(f"[2/4] Cluster sparsity: {sparsity:.3f}")
        
        if sparsity >= self.config['sparsity_threshold']:
            logger.info(f"Sparsity threshold reached ({sparsity:.3f} >= {self.config['sparsity_threshold']}). Stopping.")
            return []
        
        # Step 3: Create communities
        logger.info(f"[3/4] Creating {n_clusters} community summaries...")
        communities = []
        
        for cluster_id in range(n_clusters):
            # Get cluster members
            member_indices = [i for i, label_list in enumerate(labels) if cluster_id in label_list]
            members = [input_entities[i] for i in member_indices]
            member_probs = [probs[i, cluster_id] for i in member_indices]
            
            logger.info(f"  Cluster {cluster_id}: {len(members)} members")
            
            # LLM summarization
            try:
                community = await self.summarize_cluster(
                    members, member_probs, cluster_id, layer
                )
                communities.append(community)
                logger.info(f"  ✓ Community created: {community['title'][:50]}...")
            except Exception as e:
                logger.error(f"  ✗ Failed to summarize cluster {cluster_id}: {e}")
                continue
        
        logger.info(f"[4/4] Created {len(communities)} communities for Layer {layer}")
        
        return communities
    
    async def summarize_cluster(
        self,
        members: List[Dict[str, Any]],
        probs: List[float],
        cluster_id: int,
        layer: int
    ) -> Dict[str, Any]:
        """
        Generate community summary using LLM
        
        Args:
            members: Cluster member entities
            probs: GMM probabilities for each member
            cluster_id: Cluster number
            layer: Layer number
            
        Returns:
            Community dict
        """
        # Prepare member descriptions
        member_descriptions = []
        for member, prob in zip(members, probs):
            name = member.get('entity_name', member.get('title', 'Unknown'))
            desc = member.get('description', member.get('summary', ''))
            member_descriptions.append(
                f"- {name} (score: {prob:.2f}): {desc[:200]}"
            )
        
        # Create prompt
        prompt = f"""Bạn là chuyên gia phân tích văn bản pháp luật Việt Nam.

Dưới đây là một nhóm {len(members)} thực thể/khái niệm được gom cụm theo mức độ tương đồng ngữ nghĩa:

{chr(10).join(member_descriptions)}

Hãy tạo một báo cáo tóm tắt (community report) cho nhóm này với cấu trúc sau:

1. **Tiêu đề (title)**: Một cụm từ ngắn gọn (5-10 từ) mô tả chủ đề chính của nhóm
2. **Tóm tắt (summary)**: Mô tả ngắn gọn (2-3 câu) về nội dung chính của nhóm
3. **Các phát hiện chính (findings)**: Liệt kê 2-4 điểm quan trọng, mỗi điểm gồm:
   - summary: Tiêu đề ngắn gọn
   - explanation: Giải thích chi tiết (1-2 câu)
4. **Đánh giá (rating)**: Cho điểm từ 0-10 về tầm quan trọng của nhóm này

Trả về ĐÚNG format JSON sau (không có markdown, chỉ JSON thuần):
{{
    "title": "...",
    "summary": "...",
    "findings": [
        {{"summary": "...", "explanation": "..."}},
        {{"summary": "...", "explanation": "..."}}
    ],
    "rating": 8.5
}}"""
        
        # LLM call
        try:
            response = await self.llm_func(prompt)
            
            # Parse JSON (remove markdown if present)
            response_clean = response.strip()
            if response_clean.startswith('```'):
                # Remove markdown code blocks
                lines = response_clean.split('\n')
                response_clean = '\n'.join(lines[1:-1]) if len(lines) > 2 else response_clean
                response_clean = response_clean.replace('```json', '').replace('```', '').strip()
            
            report = json.loads(response_clean)
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM JSON response: {e}")
            logger.warning(f"Raw response: {response[:200]}...")
            # Fallback report
            report = {
                "title": f"Community {cluster_id}",
                "summary": f"Group of {len(members)} related entities",
                "findings": [
                    {"summary": "Main entities", "explanation": ", ".join([m.get('entity_name', 'Unknown') for m in members[:5]])}
                ],
                "rating": 5.0
            }
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise
        
        # Create embedding for community
        community_text = f"{report['title']}\n{report['summary']}"
        try:
            embedding = await self.embed_func([community_text])
            community_embedding = embedding[0] if isinstance(embedding[0], list) else embedding[0].tolist()
        except Exception as e:
            logger.error(f"Failed to create embedding: {e}")
            # Use average of member embeddings as fallback
            member_embeddings = [m['embedding'] for m in members]
            community_embedding = np.mean(member_embeddings, axis=0).tolist()
        
        # Build community object
        community = {
            'id': f"community_L{layer}_C{cluster_id}",
            'layer': layer,
            'community_id': f"cluster_{cluster_id}",
            'title': report['title'],
            'summary': report['summary'],
            'report_json': report,
            'embedding': community_embedding,
            'members': [m.get('entity_name', m.get('id', '')) for m in members],
            'member_count': len(members),
            'occurrence_score': float(np.mean(probs))
        }
        
        return community
    
    async def save_layer(self, communities: List[Dict[str, Any]], layer: int):
        """
        Save communities and relationships to PostgreSQL
        
        Args:
            communities: List of community dicts
            layer: Layer number
        """
        logger.info(f"Saving Layer {layer} to PostgreSQL...")
        
        for comm in communities:
            # Save community
            success = await self.storage.save_community(comm)
            if not success:
                logger.warning(f"Failed to save community: {comm['id']}")
                continue
            
            # Save memberships
            member_layer = layer - 1  # Members are from previous layer
            await self.storage.save_community_members(
                community_id=comm['id'],
                member_ids=comm['members'],
                member_layer=member_layer,
                membership_scores=[comm['occurrence_score']] * len(comm['members'])
            )
        
        logger.info(f"Layer {layer} saved successfully")
    
    async def build_full_hierarchy(self, force_rebuild: bool = False) -> Dict[str, Any]:
        """
        Build complete hierarchical structure
        
        Process:
        1. Load Layer 0 entities from PostgreSQL
        2. Iteratively build Layer 1, 2, 3... until stop condition
        3. Save each layer to PostgreSQL
        
        Args:
            force_rebuild: If True, delete existing hierarchy first
            
        Returns:
            Dict with build statistics
        """
        start_time = datetime.now()
        
        logger.info("\n" + "="*70)
        logger.info("STARTING HIERARCHICAL BUILD")
        logger.info("="*70)
        
        # Check if rebuild needed
        if not force_rebuild:
            stats = await self.storage.get_statistics()
            if stats['total_communities'] > 0:
                logger.info(f"Existing hierarchy found: {stats['total_communities']} communities")
                user_confirm = input("Rebuild? This will delete existing data. (yes/no): ")
                if user_confirm.lower() != 'yes':
                    logger.info("Build cancelled by user")
                    return stats
        
        # Delete existing hierarchy
        if force_rebuild:
            logger.info("Deleting existing hierarchical data...")
            await self.storage.delete_all_hierarchical()
        
        # Step 1: Load Layer 0
        layer_0 = await self.load_layer_0_entities()
        if not layer_0:
            logger.error("No Layer 0 entities found!")
            return {'error': 'No entities found'}
        
        logger.info(f"Layer 0: {len(layer_0)} entities loaded")
        
        # Step 2: Build layers iteratively
        all_layers = [layer_0]
        current_layer = layer_0
        layer_num = 1
        
        while layer_num <= self.config['max_layers']:
            logger.info(f"\n{'='*70}")
            logger.info(f"LAYER {layer_num} BUILD")
            logger.info(f"{'='*70}")
            
            # Build next layer
            next_layer = await self.build_layer(current_layer, layer_num)
            
            # Check stop conditions
            if not next_layer:
                logger.info(f"Stop condition reached at Layer {layer_num}")
                break
            
            if len(next_layer) <= self.config['min_entities_per_layer']:
                logger.info(f"Only {len(next_layer)} communities. Stopping.")
                break
            
            # Save layer
            await self.save_layer(next_layer, layer_num)
            
            # Prepare for next iteration
            all_layers.append(next_layer)
            current_layer = next_layer
            layer_num += 1
        
        # Build complete
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Get final statistics
        final_stats = await self.storage.get_statistics()
        
        logger.info("\n" + "="*70)
        logger.info("HIERARCHICAL BUILD COMPLETE")
        logger.info("="*70)
        logger.info(f"Total layers: {len(all_layers)}")
        logger.info(f"Total communities: {final_stats['total_communities']}")
        logger.info(f"Duration: {duration:.1f} seconds")
        
        for layer_num, layer_info in final_stats['layers'].items():
            logger.info(f"  Layer {layer_num}: {layer_info['count']} communities (avg {layer_info['avg_members']:.1f} members)")
        
        logger.info("="*70 + "\n")
        
        return final_stats
    
    async def rebuild_if_stale(self):
        """
        Rebuild hierarchy if any layer is marked as stale
        """
        stats = await self.storage.get_statistics()
        
        stale_count = sum(
            layer_info['stale_count'] 
            for layer_info in stats['layers'].values()
        )
        
        if stale_count > 0:
            logger.info(f"Found {stale_count} stale communities. Rebuilding...")
            await self.build_full_hierarchy(force_rebuild=True)
        else:
            logger.info("Hierarchy is up to date")

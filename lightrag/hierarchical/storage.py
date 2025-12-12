"""
PostgreSQL storage helpers for hierarchical communities

This module provides helper functions to interact with the PostgreSQL
database for storing and retrieving hierarchical community data.
"""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class CommunityStorage:
    """
    Helper class for community storage operations
    
    Wraps PostgreSQL operations for hierarchical communities.
    """
    
    def __init__(self, db_connection, workspace: str):
        """
        Initialize storage helper
        
        Args:
            db_connection: PostgreSQL connection (from LightRAG)
            workspace: Workspace identifier
        """
        self.db = db_connection
        self.workspace = workspace
    
    async def save_community(self, community: Dict[str, Any]) -> bool:
        """
        Save single community to PostgreSQL
        
        Args:
            community: Community dict with keys:
                - id: Unique identifier
                - layer: Layer number (1, 2, 3...)
                - community_id: Cluster identifier
                - title: Community theme
                - summary: Brief description
                - report_json: Structured report
                - embedding: Vector embedding (list)
                - member_count: Number of members
                - occurrence_score: Importance score
                
        Returns:
            True if successful, False otherwise
        """
        try:
            sql = """
                INSERT INTO lightrag_communities 
                (id, workspace, layer, community_id, title, summary, 
                 report_json, embedding, member_count, occurrence_score, 
                 is_stale, last_rebuild)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, FALSE, NOW())
                ON CONFLICT (workspace, id) DO UPDATE SET
                    title = EXCLUDED.title,
                    summary = EXCLUDED.summary,
                    report_json = EXCLUDED.report_json,
                    embedding = EXCLUDED.embedding,
                    member_count = EXCLUDED.member_count,
                    occurrence_score = EXCLUDED.occurrence_score,
                    is_stale = FALSE,
                    last_rebuild = NOW(),
                    update_time = NOW()
            """
            
            # Convert embedding to JSON string for pgvector
            embedding_json = json.dumps(community['embedding'])
            
            await self.db.execute(
                sql,
                community['id'],
                self.workspace,
                community['layer'],
                community['community_id'],
                community['title'],
                community['summary'],
                json.dumps(community['report_json']),
                embedding_json,
                community.get('member_count', 0),
                community.get('occurrence_score', 0.0)
            )
            
            logger.debug(f"Saved community: {community['id']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save community {community.get('id')}: {e}")
            return False
    
    async def save_community_members(
        self,
        community_id: str,
        member_ids: List[str],
        member_layer: int,
        membership_scores: List[float] = None,
        cluster_labels: List[int] = None
    ) -> bool:
        """
        Save community membership relationships
        
        Args:
            community_id: Community ID
            member_ids: List of member entity/community IDs
            member_layer: Layer of members (0 for entities, 1+ for communities)
            membership_scores: GMM probability scores (optional)
            cluster_labels: Original cluster labels (optional)
            
        Returns:
            True if successful
        """
        try:
            sql = """
                INSERT INTO lightrag_community_members
                (workspace, community_id, member_id, member_layer, 
                 membership_score, cluster_label)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT DO NOTHING
            """
            
            if membership_scores is None:
                membership_scores = [1.0] * len(member_ids)
            if cluster_labels is None:
                cluster_labels = [0] * len(member_ids)
            
            for member_id, score, label in zip(member_ids, membership_scores, cluster_labels):
                await self.db.execute(
                    sql,
                    self.workspace,
                    community_id,
                    member_id,
                    member_layer,
                    float(score),
                    int(label)
                )
            
            logger.debug(f"Saved {len(member_ids)} members for community {community_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save members for {community_id}: {e}")
            return False
    
    async def save_hierarchy_link(
        self,
        parent_id: str,
        child_id: str,
        parent_layer: int,
        child_layer: int
    ) -> bool:
        """
        Save parent-child hierarchy relationship
        
        Args:
            parent_id: Parent community ID
            child_id: Child community/entity ID
            parent_layer: Parent layer number
            child_layer: Child layer number
            
        Returns:
            True if successful
        """
        try:
            sql = """
                INSERT INTO lightrag_community_hierarchy
                (workspace, parent_id, child_id, parent_layer, child_layer)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT DO NOTHING
            """
            
            await self.db.execute(
                sql,
                self.workspace,
                parent_id,
                child_id,
                parent_layer,
                child_layer
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to save hierarchy link {parent_id}->{child_id}: {e}")
            return False
    
    async def load_communities(self, layer: int = None) -> List[Dict[str, Any]]:
        """
        Load communities from specific layer
        
        Args:
            layer: Layer number (if None, load all layers)
            
        Returns:
            List of community dicts
        """
        try:
            if layer is not None:
                sql = """
                    SELECT id, layer, community_id, title, summary, 
                           report_json, embedding, member_count, occurrence_score,
                           is_stale, last_rebuild
                    FROM lightrag_communities
                    WHERE workspace = $1 AND layer = $2
                    ORDER BY occurrence_score DESC
                """
                rows = await self.db.fetch(sql, self.workspace, layer)
            else:
                sql = """
                    SELECT id, layer, community_id, title, summary, 
                           report_json, embedding, member_count, occurrence_score,
                           is_stale, last_rebuild
                    FROM lightrag_communities
                    WHERE workspace = $1
                    ORDER BY layer, occurrence_score DESC
                """
                rows = await self.db.fetch(sql, self.workspace)
            
            communities = []
            for row in rows:
                comm = dict(row)
                # Parse JSON fields
                if comm['report_json']:
                    comm['report_json'] = json.loads(comm['report_json'])
                if comm['embedding']:
                    comm['embedding'] = json.loads(comm['embedding'])
                communities.append(comm)
            
            logger.info(f"Loaded {len(communities)} communities from layer {layer}")
            return communities
            
        except Exception as e:
            logger.error(f"Failed to load communities: {e}")
            return []
    
    async def get_community_members(self, community_id: str) -> List[Dict[str, Any]]:
        """
        Get members of a community
        
        Args:
            community_id: Community ID
            
        Returns:
            List of member dicts with member_id, member_layer, membership_score
        """
        try:
            sql = """
                SELECT member_id, member_layer, membership_score, cluster_label
                FROM lightrag_community_members
                WHERE workspace = $1 AND community_id = $2
                ORDER BY membership_score DESC
            """
            
            rows = await self.db.fetch(sql, self.workspace, community_id)
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get members for {community_id}: {e}")
            return []
    
    async def mark_stale(self, layer: int = None) -> bool:
        """
        Mark communities as needing rebuild
        
        Args:
            layer: Layer to mark (if None, mark all layers >= 1)
            
        Returns:
            True if successful
        """
        try:
            if layer is not None:
                sql = """
                    UPDATE lightrag_communities 
                    SET is_stale = TRUE, update_time = NOW()
                    WHERE workspace = $1 AND layer = $2
                """
                await self.db.execute(sql, self.workspace, layer)
            else:
                sql = """
                    UPDATE lightrag_communities 
                    SET is_stale = TRUE, update_time = NOW()
                    WHERE workspace = $1 AND layer >= 1
                """
                await self.db.execute(sql, self.workspace)
            
            logger.info(f"Marked layer {layer} as stale")
            return True
            
        except Exception as e:
            logger.error(f"Failed to mark stale: {e}")
            return False
    
    async def delete_layer(self, layer: int) -> bool:
        """
        Delete all communities from a specific layer
        
        Args:
            layer: Layer number to delete
            
        Returns:
            True if successful
        """
        try:
            sql = """
                DELETE FROM lightrag_communities
                WHERE workspace = $1 AND layer = $2
            """
            await self.db.execute(sql, self.workspace, layer)
            
            logger.info(f"Deleted layer {layer}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete layer {layer}: {e}")
            return False
    
    async def delete_all_hierarchical(self) -> bool:
        """
        Delete all hierarchical data (Layer 1+)
        
        Returns:
            True if successful
        """
        try:
            sql = """
                DELETE FROM lightrag_communities
                WHERE workspace = $1 AND layer >= 1
            """
            await self.db.execute(sql, self.workspace)
            
            logger.info("Deleted all hierarchical data")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete hierarchical data: {e}")
            return False
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about hierarchical structure
        
        Returns:
            Dict with layer counts and other stats
        """
        try:
            sql = """
                SELECT layer, COUNT(*) as count, 
                       AVG(member_count) as avg_members,
                       SUM(CASE WHEN is_stale THEN 1 ELSE 0 END) as stale_count
                FROM lightrag_communities
                WHERE workspace = $1
                GROUP BY layer
                ORDER BY layer
            """
            
            rows = await self.db.fetch(sql, self.workspace)
            
            stats = {
                'layers': {},
                'total_communities': 0
            }
            
            for row in rows:
                layer = row['layer']
                stats['layers'][layer] = {
                    'count': row['count'],
                    'avg_members': float(row['avg_members']) if row['avg_members'] else 0,
                    'stale_count': row['stale_count']
                }
                stats['total_communities'] += row['count']
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {'layers': {}, 'total_communities': 0}

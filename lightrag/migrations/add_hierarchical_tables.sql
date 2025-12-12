-- =========================================
-- LightRAG Hierarchical Extension Migration
-- Version: 1.0
-- Date: 2025-12-12
-- =========================================

-- Description:
-- This migration adds support for hierarchical community detection
-- in LightRAG by creating three new tables:
-- 1. lightrag_communities - Store community summaries
-- 2. lightrag_community_members - Track entity-community relationships
-- 3. lightrag_community_hierarchy - Track parent-child community relationships

-- =========================================
-- TABLE 1: Communities Storage
-- =========================================

CREATE TABLE IF NOT EXISTS lightrag_communities (
    -- Primary keys
    id VARCHAR(255),
    workspace VARCHAR(255),
    
    -- Community metadata
    layer INTEGER NOT NULL,                    -- 1, 2, 3, ... (0 = base entities)
    community_id VARCHAR(255) NOT NULL,        -- Cluster identifier
    title TEXT,                                -- Community theme/topic
    summary TEXT,                              -- Brief overview
    
    -- Generated report (LLM output)
    report_json JSONB,                         -- Structured report
    /*
    Example report_json structure:
    {
        "title": "Quy trình cấp giấy phép thăm dò",
        "summary": "Tổng hợp các quy định về thủ tục và điều kiện cấp phép...",
        "findings": [
            {
                "summary": "Điều kiện cấp phép",
                "explanation": "Tổ chức/cá nhân phải đáp ứng..."
            },
            {
                "summary": "Thủ tục nộp hồ sơ",
                "explanation": "Hồ sơ bao gồm..."
            }
        ],
        "rating": 8.5
    }
    */
    
    -- Embeddings for vector retrieval
    embedding VECTOR(1536),                    -- Summary embedding for search
    
    -- Statistics
    member_count INTEGER,                      -- Number of member entities
    occurrence_score FLOAT,                    -- Importance/centrality score
    
    -- Status tracking
    is_stale BOOLEAN DEFAULT FALSE,            -- Needs rebuild?
    last_rebuild TIMESTAMP,                    -- Last computation timestamp
    
    -- Timestamps
    create_time TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (workspace, id)
);

-- Indexes for communities
CREATE INDEX IF NOT EXISTS idx_communities_layer 
    ON lightrag_communities(workspace, layer);

CREATE INDEX IF NOT EXISTS idx_communities_stale 
    ON lightrag_communities(workspace, is_stale) 
    WHERE is_stale = TRUE;

-- Vector index for similarity search (HNSW)
CREATE INDEX IF NOT EXISTS idx_communities_embedding 
    ON lightrag_communities 
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Full-text search on title
CREATE INDEX IF NOT EXISTS idx_communities_title 
    ON lightrag_communities 
    USING GIN(to_tsvector('english', title));

-- =========================================
-- TABLE 2: Community Membership
-- =========================================

CREATE TABLE IF NOT EXISTS lightrag_community_members (
    id SERIAL,
    workspace VARCHAR(255),
    
    -- Relationship
    community_id VARCHAR(255) NOT NULL,        -- FK to lightrag_communities.id
    member_id VARCHAR(255) NOT NULL,           -- Entity or community ID
    member_layer INTEGER NOT NULL,             -- 0=entity, 1=L1 community, 2=L2...
    
    -- Clustering metadata
    membership_score FLOAT,                    -- GMM probability (0-1)
    cluster_label INTEGER,                     -- Original cluster number
    
    create_time TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (id),
    
    -- Foreign key with cascade delete
    FOREIGN KEY (workspace, community_id) 
        REFERENCES lightrag_communities(workspace, id) 
        ON DELETE CASCADE
);

-- Indexes for membership lookups
CREATE INDEX IF NOT EXISTS idx_members_community 
    ON lightrag_community_members(workspace, community_id);

CREATE INDEX IF NOT EXISTS idx_members_entity 
    ON lightrag_community_members(workspace, member_id, member_layer);

-- Unique constraint: one member can only belong to one community per layer
CREATE UNIQUE INDEX IF NOT EXISTS idx_members_unique 
    ON lightrag_community_members(workspace, member_id, member_layer, community_id);

-- =========================================
-- TABLE 3: Community Hierarchy
-- =========================================

CREATE TABLE IF NOT EXISTS lightrag_community_hierarchy (
    id SERIAL,
    workspace VARCHAR(255),
    
    -- Parent-child relationship
    parent_id VARCHAR(255) NOT NULL,           -- Layer N+1 community
    child_id VARCHAR(255) NOT NULL,            -- Layer N community/entity
    parent_layer INTEGER NOT NULL,
    child_layer INTEGER NOT NULL,
    
    create_time TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (id),
    
    -- Foreign key to parent community
    FOREIGN KEY (workspace, parent_id) 
        REFERENCES lightrag_communities(workspace, id) 
        ON DELETE CASCADE,
    
    -- Constraint: parent layer must be exactly child layer + 1
    CONSTRAINT check_hierarchy 
        CHECK (parent_layer = child_layer + 1)
);

-- Indexes for hierarchy traversal
CREATE INDEX IF NOT EXISTS idx_hierarchy_parent 
    ON lightrag_community_hierarchy(workspace, parent_id);

CREATE INDEX IF NOT EXISTS idx_hierarchy_child 
    ON lightrag_community_hierarchy(workspace, child_id);

-- Unique constraint: one child can only have one parent
CREATE UNIQUE INDEX IF NOT EXISTS idx_hierarchy_unique 
    ON lightrag_community_hierarchy(workspace, child_id);

-- =========================================
-- VERIFICATION QUERIES
-- =========================================

-- Check if tables exist
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables 
               WHERE table_name = 'lightrag_communities') THEN
        RAISE NOTICE '✅ Table lightrag_communities created';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables 
               WHERE table_name = 'lightrag_community_members') THEN
        RAISE NOTICE '✅ Table lightrag_community_members created';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables 
               WHERE table_name = 'lightrag_community_hierarchy') THEN
        RAISE NOTICE '✅ Table lightrag_community_hierarchy created';
    END IF;
    
    RAISE NOTICE '✅ Migration complete!';
END $$;

-- =========================================
-- ROLLBACK SCRIPT (if needed)
-- =========================================

-- Uncomment to rollback:
-- DROP TABLE IF EXISTS lightrag_community_hierarchy CASCADE;
-- DROP TABLE IF EXISTS lightrag_community_members CASCADE;
-- DROP TABLE IF EXISTS lightrag_communities CASCADE;

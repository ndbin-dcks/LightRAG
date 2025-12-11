#!/usr/bin/env python3
"""
LightRAG Migration Script: NanoVectorDB → PostgreSQL
Migrates 3,795 entities + 3,409 relationships from JSON files to PostgreSQL

Usage:
    python migrate_nano_to_pg.py
"""

import json
import asyncio
import sys
from pathlib import Path
from datetime import datetime
import asyncpg

# ══════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════

# Source: NanoVectorDB (JSON files)
SOURCE_DIR = "/opt/lightrag/data/rag_storage"

# Target: PostgreSQL
PG_CONFIG = {
    "host": "n8n-postgres-1",
    "port": 5432,
    "database": "lightrag_db",
    "user": "user_76e9fdf7564ff5fb",
    "password": "b35066096c2c07c03ae8f6030ce835d39c8f50adf34da4bd"
}

# Files to migrate
FILES = {
    "entities": f"{SOURCE_DIR}/vdb_entities.json",
    "relationships": f"{SOURCE_DIR}/vdb_relationships.json",
    "chunks": f"{SOURCE_DIR}/vdb_chunks.json",
    "text_chunks": f"{SOURCE_DIR}/kv_store_text_chunks.json",
    "full_docs": f"{SOURCE_DIR}/kv_store_full_docs.json",
    "full_entities": f"{SOURCE_DIR}/kv_store_full_entities.json",
    "full_relations": f"{SOURCE_DIR}/kv_store_full_relations.json",
    "llm_cache": f"{SOURCE_DIR}/kv_store_llm_response_cache.json",
}

# ══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════

def print_header(text):
    """Print section header"""
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}")

def print_progress(current, total, prefix="Progress"):
    """Print progress bar"""
    percent = int((current / total) * 100) if total > 0 else 0
    bar_length = 50
    filled = int(bar_length * current / total) if total > 0 else 0
    bar = '█' * filled + '░' * (bar_length - filled)
    print(f"\r{prefix}: |{bar}| {percent}% ({current}/{total})", end='', flush=True)
    if current >= total:
        print()  # New line when complete

# ══════════════════════════════════════════════════════════════
# DATABASE SETUP
# ══════════════════════════════════════════════════════════════

async def create_tables(conn):
    """Create necessary tables in PostgreSQL"""
    print_header("Creating Database Tables")
    
    # Table for vector storage (entities, relationships, chunks)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS vector_storage (
            id TEXT PRIMARY KEY,
            namespace TEXT NOT NULL,
            embedding vector(1536),
            content TEXT,
            metadata JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    print("✅ Created table: vector_storage")
    
    # Table for KV storage
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS kv_storage (
            id TEXT PRIMARY KEY,
            namespace TEXT NOT NULL,
            value JSONB NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    print("✅ Created table: kv_storage")
    
    # Create indexes
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_vector_namespace 
        ON vector_storage(namespace);
    """)
    
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_kv_namespace 
        ON kv_storage(namespace);
    """)
    
    # Vector similarity search index (HNSW)
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_vector_embedding 
        ON vector_storage 
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
    """)
    print("✅ Created indexes")

# ══════════════════════════════════════════════════════════════
# MIGRATION FUNCTIONS
# ══════════════════════════════════════════════════════════════

async def migrate_vector_storage(conn, filepath, namespace):
    """Migrate vector storage (entities/relationships/chunks)"""
    print_header(f"Migrating: {namespace}")
    
    # Read JSON file
    print(f"📖 Reading: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, dict) or 'data' not in data:
        print(f"⚠️  Invalid format in {filepath}")
        return 0
    
    items = data['data']
    total = len(items)
    print(f"✅ Found {total} items")
    
    if total == 0:
        return 0
    
    # Prepare batch insert
    print(f"💾 Inserting into PostgreSQL...")
    
    inserted = 0
    batch_size = 100
    
    for i in range(0, total, batch_size):
        batch = items[i:i + batch_size]
        
        for item in batch:
            item_id = item.get('__id__')
            if not item_id:
                continue
            
            # Extract embedding
            embedding = item.get('__vector__')
            if embedding:
                embedding = str(embedding)  # Convert list to string for PostgreSQL
            
            # Extract metadata (remove internal fields)
            metadata = {k: v for k, v in item.items() 
                       if not k.startswith('__')}
            
            # Get content
            content = metadata.get('description', '') or metadata.get('content', '')
            
            # Insert
            try:
                await conn.execute("""
                    INSERT INTO vector_storage (id, namespace, embedding, content, metadata)
                    VALUES ($1, $2, $3::vector, $4, $5)
                    ON CONFLICT (id) DO UPDATE 
                    SET embedding = EXCLUDED.embedding,
                        content = EXCLUDED.content,
                        metadata = EXCLUDED.metadata,
                        updated_at = CURRENT_TIMESTAMP
                """, item_id, namespace, embedding, content, json.dumps(metadata))
                
                inserted += 1
                
            except Exception as e:
                print(f"\n⚠️  Error inserting {item_id}: {e}")
        
        print_progress(min(i + batch_size, total), total, "Inserting")
    
    print(f"\n✅ Migrated {inserted}/{total} items to {namespace}")
    return inserted


async def migrate_kv_storage(conn, filepath, namespace):
    """Migrate KV storage"""
    print_header(f"Migrating KV: {namespace}")
    
    # Read JSON file
    print(f"📖 Reading: {filepath}")
    
    if not Path(filepath).exists():
        print(f"⚠️  File not found: {filepath}")
        return 0
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, dict):
        print(f"⚠️  Invalid format in {filepath}")
        return 0
    
    total = len(data)
    print(f"✅ Found {total} items")
    
    if total == 0:
        return 0
    
    # Insert
    print(f"💾 Inserting into PostgreSQL...")
    
    inserted = 0
    for i, (key, value) in enumerate(data.items(), 1):
        try:
            await conn.execute("""
                INSERT INTO kv_storage (id, namespace, value)
                VALUES ($1, $2, $3)
                ON CONFLICT (id) DO UPDATE 
                SET value = EXCLUDED.value,
                    updated_at = CURRENT_TIMESTAMP
            """, key, namespace, json.dumps(value))
            
            inserted += 1
            print_progress(i, total, "Inserting")
            
        except Exception as e:
            print(f"\n⚠️  Error inserting {key}: {e}")
    
    print(f"\n✅ Migrated {inserted}/{total} items to {namespace}")
    return inserted

# ══════════════════════════════════════════════════════════════
# VERIFICATION
# ══════════════════════════════════════════════════════════════

async def verify_migration(conn):
    """Verify migration results"""
    print_header("Verification")
    
    # Count entities
    entities_count = await conn.fetchval("""
        SELECT COUNT(*) FROM vector_storage WHERE namespace = 'entities'
    """)
    print(f"✅ Entities: {entities_count}")
    
    # Count relationships
    relationships_count = await conn.fetchval("""
        SELECT COUNT(*) FROM vector_storage WHERE namespace = 'relationships'
    """)
    print(f"✅ Relationships: {relationships_count}")
    
    # Count chunks
    chunks_count = await conn.fetchval("""
        SELECT COUNT(*) FROM vector_storage WHERE namespace = 'chunks'
    """)
    print(f"✅ Chunks: {chunks_count}")
    
    # Count KV items
    kv_count = await conn.fetchval("""
        SELECT COUNT(*) FROM kv_storage
    """)
    print(f"✅ KV Storage items: {kv_count}")
    
    # Database size
    db_size = await conn.fetchval("""
        SELECT pg_size_pretty(pg_database_size('lightrag_db'))
    """)
    print(f"✅ Database size: {db_size}")
    
    return {
        'entities': entities_count,
        'relationships': relationships_count,
        'chunks': chunks_count,
        'kv_items': kv_count,
        'db_size': db_size
    }

# ══════════════════════════════════════════════════════════════
# MAIN MIGRATION
# ══════════════════════════════════════════════════════════════

async def main():
    """Main migration function"""
    print()
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "LIGHTRAG MIGRATION: NANO → POSTGRESQL" + " " * 15 + "║")
    print("║" + " " * 68 + "║")
    print("║" + f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".ljust(68) + "║")
    print("╚" + "═" * 68 + "╝")
    
    stats = {
        'entities': 0,
        'relationships': 0,
        'chunks': 0,
        'kv_items': 0
    }
    
    try:
        # Connect to PostgreSQL
        print_header("Connecting to PostgreSQL")
        print(f"Host: {PG_CONFIG['host']}")
        print(f"Database: {PG_CONFIG['database']}")
        
        conn = await asyncpg.connect(**PG_CONFIG)
        print("✅ Connected successfully")
        
        # Create tables
        await create_tables(conn)
        
        # Migrate vector storage
        stats['entities'] = await migrate_vector_storage(
            conn, FILES['entities'], 'entities'
        )
        
        stats['relationships'] = await migrate_vector_storage(
            conn, FILES['relationships'], 'relationships'
        )
        
        stats['chunks'] = await migrate_vector_storage(
            conn, FILES['chunks'], 'chunks'
        )
        
        # Migrate KV storage
        for key, filepath in [
            ('text_chunks', FILES['text_chunks']),
            ('full_docs', FILES['full_docs']),
            ('full_entities', FILES['full_entities']),
            ('full_relations', FILES['full_relations']),
            ('llm_cache', FILES['llm_cache']),
        ]:
            count = await migrate_kv_storage(conn, filepath, key)
            stats['kv_items'] += count
        
        # Verify
        verification = await verify_migration(conn)
        
        # Close connection
        await conn.close()
        
        # Summary
        print()
        print("╔" + "═" * 68 + "╗")
        print("║" + " " * 23 + "MIGRATION SUMMARY" + " " * 28 + "║")
        print("╠" + "═" * 68 + "╣")
        print("║" + f"  Entities migrated: {stats['entities']}".ljust(68) + "║")
        print("║" + f"  Relationships migrated: {stats['relationships']}".ljust(68) + "║")
        print("║" + f"  Chunks migrated: {stats['chunks']}".ljust(68) + "║")
        print("║" + f"  KV items migrated: {stats['kv_items']}".ljust(68) + "║")
        print("║" + " " * 68 + "║")
        print("║" + f"  Database size: {verification['db_size']}".ljust(68) + "║")
        print("║" + f"  Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".ljust(68) + "║")
        print("║" + " " * 68 + "║")
        print("║" + "  Status: ✅ SUCCESS".ljust(68) + "║")
        print("╚" + "═" * 68 + "╝")
        
        return True
        
    except Exception as e:
        print()
        print("╔" + "═" * 68 + "╗")
        print("║" + " " * 26 + "ERROR OCCURRED" + " " * 29 + "║")
        print("╠" + "═" * 68 + "╣")
        print("║" + f"  {str(e)[:66]}".ljust(68) + "║")
        print("║" + " " * 68 + "║")
        print("║" + "  Status: ❌ FAILED".ljust(68) + "║")
        print("╚" + "═" * 68 + "╝")
        
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
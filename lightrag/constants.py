"""
Centralized configuration constants for LightRAG.

This module defines default values for configuration constants used across
different parts of the LightRAG system. Centralizing these values ensures
consistency and makes maintenance easier.

CUSTOMIZED FOR: Vietnamese Legal Documents (Luật Địa chất và Khoáng sản)
"""

# Default values for server settings
DEFAULT_WOKERS = 2
DEFAULT_MAX_GRAPH_NODES = 5000  # Tăng từ 1000 để phù hợp với văn bản pháp luật dày đặc

# Default values for extraction settings
DEFAULT_SUMMARY_LANGUAGE = "Vietnamese"  # Changed from "English" to "Vietnamese"
DEFAULT_MAX_GLEANING = 1

# Number of description fragments to trigger LLM summary
DEFAULT_FORCE_LLM_SUMMARY_ON_MERGE = 8
# Max description token size to trigger LLM summary
DEFAULT_SUMMARY_MAX_TOKENS = 1200
# Recommended LLM summary output length in tokens
DEFAULT_SUMMARY_LENGTH_RECOMMENDED = 600
# Maximum token size sent to LLM for summary
DEFAULT_SUMMARY_CONTEXT_SIZE = 12000

# =============================================================================
# ENTITY TYPES FOR VIETNAMESE LEGAL DOCUMENTS
# Optimized for: Luật Địa chất và Khoáng sản (54/2024/QH15) & Nghị định 193
# =============================================================================
DEFAULT_ENTITY_TYPES = [
    # --- CẤU TRÚC VĂN BẢN (5) ---
    "LegalDocument",      # Luật 54, NĐ 193, Thông tư...
    "Chapter",            # Chương
    "Article",            # Điều
    "Clause",             # Khoản
    "Point",              # Điểm
    
    # --- CHỦ THỂ (3) ---
    "Organization",       # Bộ NN&MT, UBND tỉnh, Cục, Sở
    "Council",            # Hội đồng thẩm định/đánh giá
    "Subject",            # DN, HTX, Cá nhân (người thực hiện)
    
    # --- ĐỐI TƯỢNG KHOÁNG SẢN (3) ---
    "MineralGroup",       # Nhóm I, II, III, IV
    "SpecialMineral",     # Chiến lược, quan trọng, phóng xạ, độc hại
    "WasteProduct",       # Đất đá thải, quặng đuôi
    
    # --- HỒ SƠ & PHÁP LÝ (3) ---
    "License",            # Giấy phép thăm dò/khai thác
    "TechnicalDoc",       # Đề án thăm dò, Thiết kế mỏ, Đề án đóng cửa mỏ
    "Dossier",            # Hồ sơ (tập hợp các tài liệu nộp)
    
    # --- KHÔNG GIAN & THỜI GIAN (3) ---
    "ManagementArea",     # Khu vực cấm, dự trữ, đấu giá...
    "TimeDuration",       # 30 ngày, 12 tháng, 20 năm (thời hạn)
    "Concept",            # Khái niệm chung (Tai biến, An toàn mỏ, định nghĩa Điều 2...)
    
    # --- TÀI CHÍNH (3) ---
    "FinancialObligation",# Tiền cấp quyền, Thuế, Phí môi trường
    "AuctionFee",         # Tiền đặt trước, Bước giá
    "Cost",               # Chi phí hoàn trả thăm dò (định lượng cụ thể)
    
    # --- QUY ĐỊNH & THI HÀNH (5) ---
    "Process",            # Thủ tục hành chính (Cấp phép, Gia hạn...)
    "Condition",          # Điều kiện (để được cấp phép/tham gia)
    "Criteria",           # Tiêu chí (để khoanh định khu vực/chấm điểm)
    "Obligation",         # Nghĩa vụ/Trách nhiệm (Báo cáo, nộp tiền...)
    "Violation_Penalty",  # Gộp Vi phạm & Chế tài (để giảm độ phức tạp)
]

# Separator for graph fields
GRAPH_FIELD_SEP = "<SEP>"

# Query and retrieval configuration defaults
DEFAULT_TOP_K = 40
DEFAULT_CHUNK_TOP_K = 20
DEFAULT_MAX_ENTITY_TOKENS = 6000
DEFAULT_MAX_RELATION_TOKENS = 8000
DEFAULT_MAX_TOTAL_TOKENS = 30000
DEFAULT_COSINE_THRESHOLD = 0.2
DEFAULT_RELATED_CHUNK_NUMBER = 5
DEFAULT_KG_CHUNK_PICK_METHOD = "VECTOR"

# TODO: Deprecated. All conversation_history messages is send to LLM.
DEFAULT_HISTORY_TURNS = 0

# Rerank configuration defaults
DEFAULT_MIN_RERANK_SCORE = 0.0
DEFAULT_RERANK_BINDING = "null"

# File path configuration for vector and graph database(Should not be changed, used in Milvus Schema)
DEFAULT_MAX_FILE_PATH_LENGTH = 32768

# Default temperature for LLM
DEFAULT_TEMPERATURE = 1.0

# Async configuration defaults
DEFAULT_MAX_ASYNC = 4  # Default maximum async operations
DEFAULT_MAX_PARALLEL_INSERT = 2  # Default maximum parallel insert operations

# Embedding configuration defaults
DEFAULT_EMBEDDING_FUNC_MAX_ASYNC = 8  # Default max async for embedding functions
DEFAULT_EMBEDDING_BATCH_NUM = 10  # Default batch size for embedding computations

# Gunicorn worker timeout
DEFAULT_TIMEOUT = 300

# Default llm and embedding timeout
DEFAULT_LLM_TIMEOUT = 180
DEFAULT_EMBEDDING_TIMEOUT = 30

# Logging configuration defaults
DEFAULT_LOG_MAX_BYTES = 10485760  # Default 10MB
DEFAULT_LOG_BACKUP_COUNT = 5  # Default 5 backups
DEFAULT_LOG_FILENAME = "lightrag.log"  # Default log filename

# Ollama server configuration defaults
DEFAULT_OLLAMA_MODEL_NAME = "lightrag"
DEFAULT_OLLAMA_MODEL_TAG = "latest"
DEFAULT_OLLAMA_MODEL_SIZE = 7365960935
DEFAULT_OLLAMA_CREATED_AT = "2024-01-15T00:00:00Z"
DEFAULT_OLLAMA_DIGEST = "sha256:lightrag"

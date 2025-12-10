from __future__ import annotations
from typing import Any


PROMPTS: dict[str, Any] = {}

# All delimiters must be formatted as "<|UPPER_CASE_STRING|>"
PROMPTS["DEFAULT_TUPLE_DELIMITER"] = "<|#|>"
PROMPTS["DEFAULT_COMPLETION_DELIMITER"] = "<|COMPLETE|>"

# =============================================================================
# ENTITY EXTRACTION SYSTEM PROMPT - ENHANCED FOR VIETNAMESE LEGAL DOCUMENTS
# =============================================================================
PROMPTS["entity_extraction_system_prompt"] = """---Role---
You are a Knowledge Graph Specialist responsible for extracting entities and relationships from Vietnamese legal documents about geology and minerals (Luật Địa chất và Khoáng sản).
---Input Format Description---
Dữ liệu đầu vào đã được gắn thẻ cấu trúc (Markdown-like):
- `### Điều...`: Là thực thể loại "Article" (Điều luật).
- `#### Khoản...`: Là thực thể loại "Clause" (Khoản).
- `##### Điểm...`: Là thực thể loại "Point" (Điểm).
---Entity Type Descriptions (Mô tả loại thực thể)---

1. **LegalDocument** - Văn bản pháp luật gốc
   - Luật, Nghị định, Thông tư, Quyết định
   - VD: "Luật Địa chất và khoáng sản số 54/2024/QH15", "Nghị định 193/2024/NĐ-CP"

2. **Chapter** - Chương trong văn bản pháp luật
   - VD: "Chương I - Những quy định chung", "Chương VI - Quản lý khoáng sản chiến lược"

3. **Article** - Điều - đơn vị quy định cơ bản
   - VD: "Điều 2", "Điều 35", "Điều 108"
   - QUAN TRỌNG: Phải kèm tên văn bản khi tham chiếu chéo

4. **Clause** - Khoản - chi tiết trong Điều
   - VD: "Khoản 1 Điều 4", "Khoản 2 Điều 35"

5. **Point** - Điểm - chi tiết trong Khoản
   - VD: "Điểm a khoản 2 Điều 4", "Điểm đ khoản 1 Điều 59"

6. **Organization** - Cơ quan nhà nước có thẩm quyền
   - VD: "Chính phủ", "Bộ Tài nguyên và Môi trường", "UBND cấp tỉnh"

7. **Council** - Hội đồng thẩm định, đánh giá
   - VD: "Hội đồng đánh giá trữ lượng khoáng sản quốc gia"

8. **Subject** - Tổ chức, cá nhân thực hiện hoạt động khoáng sản
   - VD: "Tổ chức, cá nhân khai thác khoáng sản", "Doanh nghiệp thăm dò"

9. **MineralGroup** - Nhóm khoáng sản (I, II, III, IV)
   - VD: "Khoáng sản nhóm I", "Khoáng sản nhóm II"

10. **SpecialMineral** - Khoáng sản đặc biệt
    - VD: "Khoáng sản chiến lược, quan trọng", "Khoáng sản phóng xạ"

11. **WasteProduct** - Sản phẩm phụ, chất thải mỏ
    - VD: "Đất đá thải mỏ", "Quặng đuôi"

12. **License** - Giấy phép hoạt động khoáng sản
    - VD: "Giấy phép thăm dò khoáng sản", "Giấy phép khai thác khoáng sản"

13. **TechnicalDoc** - Tài liệu kỹ thuật
    - VD: "Đề án thăm dò khoáng sản", "Thiết kế mỏ"

14. **Dossier** - Hồ sơ hành chính
    - VD: "Hồ sơ đề nghị cấp phép", "Hồ sơ đấu giá"

15. **ManagementArea** - Khu vực quản lý khoáng sản
    - VD: "Khu vực cấm hoạt động khoáng sản", "Khu vực dự trữ khoáng sản quốc gia"

16. **TimeDuration** - Thời hạn, thời gian
    - VD: "48 tháng", "30 năm", "20 ngày làm việc"

17. **Concept** - Khái niệm, định nghĩa trong văn bản pháp luật
    - VD: "Địa chất", "Tai biến địa chất", "Thăm dò khoáng sản"

18. **FinancialObligation** - Nghĩa vụ tài chính
    - VD: "Tiền cấp quyền khai thác khoáng sản", "Thuế tài nguyên"

19. **AuctionFee** - Phí liên quan đến đấu giá
    - VD: "Tiền đặt trước", "Bước giá", "Giá khởi điểm"

20. **Cost** - Chi phí cụ thể
    - VD: "Chi phí thăm dò do Nhà nước đầu tư"

21. **Process** - Quy trình, thủ tục hành chính
    - VD: "Thủ tục cấp giấy phép", "Quy trình đấu giá"

22. **Condition** - Điều kiện
    - VD: "Điều kiện cấp giấy phép thăm dò"

23. **Criteria** - Tiêu chí
    - VD: "Tiêu chí khoanh định khu vực"

24. **Obligation** - Nghĩa vụ, trách nhiệm
    - VD: "Nghĩa vụ báo cáo", "Trách nhiệm bảo vệ môi trường"

25. **Violation_Penalty** - Vi phạm và chế tài xử lý
    - VD: "Thu hồi giấy phép", "Đình chỉ hoạt động"


---Instructions---
0.  **Markdown Structural Parsing (Xử lý Cấu trúc Markdown - ƯU TIÊN):**
    * **Nhận diện:** Nếu dòng văn bản bắt đầu bằng ký tự Markdown (`###`, `####`, `#####`), đây là định danh duy nhất (Unique ID) của thực thể cấu trúc.
    * **Entity Name:** BẮT BUỘC loại bỏ toàn bộ chuỗi ký tự `#` đầu dòng.
        * Ví dụ Input: `#### Khoản 1 Điều 1 Luật 54/2024/QH15. Phạm vi điều chỉnh`
        * Output Entity Name: `Khoản 1 Điều 1 Luật 54/2024/QH15` (Xóa các dấu #).
    * **Entity Type Mapping:**
        * `### ...` -> Type: `Article`
        * `#### ...` -> Type: `Clause`
        * `##### ...` -> Type: `Point`
    * **Quan hệ Cấu trúc (Structural Relationships):**
        * Tự động tạo quan hệ phân cấp dựa trên số lượng dấu `#`:
        * Entity `##### ...` --(thuộc)--> Entity `#### ...` (gần nhất phía trên).
        * Entity `#### ...` --(thuộc)--> Entity `### ...` (gần nhất phía trên).
1.  **Entity Extraction & Output:**
    *   **Identification:** Identify clearly defined and meaningful entities in the input text.
    *   **Entity Details:** For each identified entity, extract:
        *   entity_name: The name of the entity (exact Vietnamese name)
        *   entity_type: One of the types above, or Concept if none apply
        *   entity_description: Concise description based on the input text
    *   **Output Format - Entities:** 4 fields delimited by {tuple_delimiter}:
        *   Format: entity{tuple_delimiter}entity_name{tuple_delimiter}entity_type{tuple_delimiter}entity_description

2.  **Relationship Extraction & Output:**
    *   **Identification:** Identify direct relationships between extracted entities.
    *   **Cross-Reference Detection:** Pay attention to:
        *   "quy định tại Điều X" → keyword "tham chiếu"
        *   "theo quy định tại khoản Y Điều X" → keyword "tham chiếu"
    *   **Relationship Details:** For each relationship:
        *   source_entity: Name of source entity
        *   target_entity: Name of target entity
        *   relationship_keywords: Vietnamese keywords like "quy định", "tham chiếu", "bao gồm"
        *   relationship_description: Concise explanation
    *   **Output Format - Relationships:** 5 fields delimited by {tuple_delimiter}:
        *   Format: relation{tuple_delimiter}source_entity{tuple_delimiter}target_entity{tuple_delimiter}relationship_keywords{tuple_delimiter}relationship_description

3.  **Delimiter Usage:** The {tuple_delimiter} is a field separator only.

4.  **Output Order:** Output all entities first, then all relationships.

5.  **Context:** Avoid pronouns like "Luật này". Resolve to actual names.

6.  **Language:** Output in {language}. Keep Vietnamese legal terms.

7.  **Completion:** Output {completion_delimiter} when done.

---Examples---
{examples}

---Real Data to be Processed---
<Input>
Entity_types: [{entity_types}]
Text:
{input_text}
"""

# =============================================================================
# EXAMPLES
# =============================================================================
PROMPTS["entity_extraction_examples"] = [
    """<Input Text>
Điều 2. Giải thích từ ngữ
Trong Luật này, các từ ngữ dưới đây được hiểu như sau:
9. Tai biến địa chất là hiện tượng tự nhiên bất thường có thể gây thiệt hại.
21. Hoạt động khoáng sản bao gồm thăm dò khoáng sản, khai thác khoáng sản, đóng cửa mỏ khoáng sản.

<o>
entity{tuple_delimiter}Luật Địa chất và khoáng sản{tuple_delimiter}LegalDocument{tuple_delimiter}Văn bản luật quy định về địa chất và khoáng sản
entity{tuple_delimiter}Điều 2 Luật Địa chất và khoáng sản{tuple_delimiter}Article{tuple_delimiter}Điều giải thích từ ngữ
entity{tuple_delimiter}Tai biến địa chất{tuple_delimiter}Concept{tuple_delimiter}Hiện tượng tự nhiên bất thường có thể gây thiệt hại
entity{tuple_delimiter}Hoạt động khoáng sản{tuple_delimiter}Concept{tuple_delimiter}Bao gồm thăm dò, khai thác, đóng cửa mỏ khoáng sản
entity{tuple_delimiter}Thăm dò khoáng sản{tuple_delimiter}Concept{tuple_delimiter}Một trong ba hoạt động khoáng sản
entity{tuple_delimiter}Khai thác khoáng sản{tuple_delimiter}Concept{tuple_delimiter}Một trong ba hoạt động khoáng sản
relation{tuple_delimiter}Điều 2 Luật Địa chất và khoáng sản{tuple_delimiter}Tai biến địa chất{tuple_delimiter}định nghĩa{tuple_delimiter}Điều 2 định nghĩa khái niệm Tai biến địa chất
relation{tuple_delimiter}Điều 2 Luật Địa chất và khoáng sản{tuple_delimiter}Hoạt động khoáng sản{tuple_delimiter}định nghĩa{tuple_delimiter}Điều 2 định nghĩa khái niệm Hoạt động khoáng sản
relation{tuple_delimiter}Hoạt động khoáng sản{tuple_delimiter}Thăm dò khoáng sản{tuple_delimiter}bao gồm{tuple_delimiter}Hoạt động khoáng sản bao gồm thăm dò khoáng sản
relation{tuple_delimiter}Hoạt động khoáng sản{tuple_delimiter}Khai thác khoáng sản{tuple_delimiter}bao gồm{tuple_delimiter}Hoạt động khoáng sản bao gồm khai thác khoáng sản
{completion_delimiter}
""",
    """<Input Text>
Điều 35. Thăm dò xuống sâu và mở rộng
1. Khu vực khoáng sản được xem xét cấp giấy phép thăm dò xuống sâu quy định tại điểm đ khoản 2 Điều 4 của Luật Địa chất và khoáng sản phải đáp ứng các yêu cầu sau:
a) Bảo đảm quy định tại khoản 3 Điều 12 của Luật Địa chất và khoáng sản;

<o>
entity{tuple_delimiter}Nghị định 193/2024/NĐ-CP{tuple_delimiter}LegalDocument{tuple_delimiter}Nghị định hướng dẫn thi hành Luật
entity{tuple_delimiter}Điều 35 Nghị định 193{tuple_delimiter}Article{tuple_delimiter}Điều quy định về thăm dò xuống sâu và mở rộng
entity{tuple_delimiter}Luật Địa chất và khoáng sản{tuple_delimiter}LegalDocument{tuple_delimiter}Văn bản luật về địa chất và khoáng sản
entity{tuple_delimiter}Điểm đ khoản 2 Điều 4 Luật Địa chất và khoáng sản{tuple_delimiter}Point{tuple_delimiter}Điểm quy định về khu vực thăm dò
entity{tuple_delimiter}Khoản 3 Điều 12 Luật Địa chất và khoáng sản{tuple_delimiter}Clause{tuple_delimiter}Khoản quy định điều kiện
relation{tuple_delimiter}Điều 35 Nghị định 193{tuple_delimiter}Điểm đ khoản 2 Điều 4 Luật Địa chất và khoáng sản{tuple_delimiter}tham chiếu{tuple_delimiter}Điều 35 tham chiếu đến quy định tại Luật
relation{tuple_delimiter}Điều 35 Nghị định 193{tuple_delimiter}Khoản 3 Điều 12 Luật Địa chất và khoáng sản{tuple_delimiter}tham chiếu{tuple_delimiter}Điều 35 yêu cầu bảo đảm quy định tại khoản 3 Điều 12
relation{tuple_delimiter}Nghị định 193/2024/NĐ-CP{tuple_delimiter}Luật Địa chất và khoáng sản{tuple_delimiter}hướng dẫn{tuple_delimiter}Nghị định 193 hướng dẫn thi hành Luật
{completion_delimiter}
""",
    """<Input Text>
Điều 108. Thẩm quyền cấp, gia hạn, điều chỉnh, thu hồi giấy phép
1. Bộ Tài nguyên và Môi trường cấp giấy phép đối với khoáng sản nhóm I, nhóm II.
2. UBND cấp tỉnh cấp giấy phép đối với khoáng sản nhóm III, nhóm IV.

<o>
entity{tuple_delimiter}Điều 108 Luật Địa chất và khoáng sản{tuple_delimiter}Article{tuple_delimiter}Điều quy định về thẩm quyền cấp phép
entity{tuple_delimiter}Bộ Tài nguyên và Môi trường{tuple_delimiter}Organization{tuple_delimiter}Cơ quan có thẩm quyền cấp phép khoáng sản nhóm I, II
entity{tuple_delimiter}UBND cấp tỉnh{tuple_delimiter}Organization{tuple_delimiter}Cơ quan có thẩm quyền cấp phép khoáng sản nhóm III, IV
entity{tuple_delimiter}Khoáng sản nhóm I{tuple_delimiter}MineralGroup{tuple_delimiter}Nhóm khoáng sản thuộc thẩm quyền Bộ TNMT
entity{tuple_delimiter}Khoáng sản nhóm II{tuple_delimiter}MineralGroup{tuple_delimiter}Nhóm khoáng sản thuộc thẩm quyền Bộ TNMT
entity{tuple_delimiter}Khoáng sản nhóm III{tuple_delimiter}MineralGroup{tuple_delimiter}Nhóm khoáng sản thuộc thẩm quyền UBND tỉnh
entity{tuple_delimiter}Khoáng sản nhóm IV{tuple_delimiter}MineralGroup{tuple_delimiter}Nhóm khoáng sản thuộc thẩm quyền UBND tỉnh
relation{tuple_delimiter}Bộ Tài nguyên và Môi trường{tuple_delimiter}Khoáng sản nhóm I{tuple_delimiter}có thẩm quyền cấp phép{tuple_delimiter}Bộ TNMT có thẩm quyền cấp phép khoáng sản nhóm I
relation{tuple_delimiter}Bộ Tài nguyên và Môi trường{tuple_delimiter}Khoáng sản nhóm II{tuple_delimiter}có thẩm quyền cấp phép{tuple_delimiter}Bộ TNMT có thẩm quyền cấp phép khoáng sản nhóm II
relation{tuple_delimiter}UBND cấp tỉnh{tuple_delimiter}Khoáng sản nhóm III{tuple_delimiter}có thẩm quyền cấp phép{tuple_delimiter}UBND tỉnh có thẩm quyền cấp phép khoáng sản nhóm III
relation{tuple_delimiter}UBND cấp tỉnh{tuple_delimiter}Khoáng sản nhóm IV{tuple_delimiter}có thẩm quyền cấp phép{tuple_delimiter}UBND tỉnh có thẩm quyền cấp phép khoáng sản nhóm IV
{completion_delimiter}
""",
]

# =============================================================================
# USER PROMPTS
# =============================================================================
PROMPTS["entity_extraction_user_prompt"] = """---Task---
Extract entities and relationships from the input text.

---Instructions---
1. Follow format requirements strictly
2. Output only entities and relationships, no explanations
3. Output {completion_delimiter} when done
4. Output language: {language}
5. Prioritize cross-references (tham chiếu)

<o>
"""

PROMPTS["entity_continue_extraction_user_prompt"] = """---Task---
Extract any missed entities and relationships.

---Instructions---
1. Do NOT re-output already extracted items
2. Entity format: 4 fields with {tuple_delimiter}
3. Relation format: 5 fields with {tuple_delimiter}
4. Output {completion_delimiter} when done
5. Output language: {language}

<o>
"""

# =============================================================================
# SUMMARY PROMPTS
# =============================================================================
PROMPTS["summarize_entity_descriptions"] = """You are a helpful assistant responsible for generating a comprehensive summary.
Given entities and descriptions, concatenate into a single comprehensive description.
Use {language} as output language.

#######
-{description_type}-
{description_name}

-----Descriptions-----
{description_list}

#######

Output a single, comprehensive, {language} description of maximum {summary_length} tokens:
"""

# =============================================================================
# QUERY PROMPTS
# =============================================================================
PROMPTS["fail_response"] = "Xin lỗi, tôi không thể tìm thấy thông tin liên quan đến câu hỏi của bạn."

PROMPTS["rag_response"] = """---Role---
Bạn là trợ lý chuyên gia về Luật Địa chất và Khoáng sản Việt Nam.

---Goal---
Tạo câu trả lời theo định dạng {response_type} để trả lời câu hỏi của người dùng.

---Guidelines---
- Trả lời bao quát các khía cạnh chính
- Nêu rõ Điều, Khoản, Điểm cụ thể
- Phần References: ### Tài liệu tham khảo

**Hướng dẫn bổ sung**: {user_prompt}

---Context---

{context_data}
"""

PROMPTS["naive_rag_response"] = """---Role---
Bạn là trợ lý chuyên gia về Luật Địa chất và Khoáng sản Việt Nam.

---Goal---
Tạo câu trả lời theo định dạng {response_type} dựa trên văn bản được cung cấp.

**Hướng dẫn bổ sung**: {user_prompt}

---Context---

{context_data}
"""

PROMPTS["kg_query_context"] = """
Knowledge Graph Data (Entity):
{entities_str}

Knowledge Graph Data (Relationship):
{relations_str}

Document Chunks:
{text_chunks_str}

Reference Document List:
{reference_list_str}
"""

PROMPTS["naive_query_context"] = """
Document Chunks:
{text_chunks_str}

Reference Document List:
{reference_list_str}
"""

# =============================================================================
# KEYWORD EXTRACTION
# =============================================================================
PROMPTS["keywords_extraction"] = """---Role---
Bạn là chuyên gia Phân tích Ngữ nghĩa và Tra cứu, Pháp luật (Legal Semantic Expert).

---Method: HyDE (Hypothetical Document Embeddings)---
Để trích xuất từ khóa chính xác, hãy thực hiện quy trình tư duy (ẩn) sau:
1. **Phân tích:** Xác định vấn đề pháp lý cốt lõi trong câu hỏi của người dùng (User Query).
2. **Mô phỏng (Simulation):** Hãy viết nháp trong đầu một đoạn văn bản mang phong cách "Văn bản quy phạm pháp luật" (Luật/Nghị định) quy định về vấn đề đó. 
   - *Lưu ý:* Không cần trả lời đúng sai cho câu hỏi, quan trọng là phải dùng đúng **Thuật ngữ chuyên ngành (Legal Terminology)** mà văn bản luật thực tế sẽ dùng.
3. **Trích xuất:** Lấy các từ khóa quan trọng nhất từ đoạn văn bản mô phỏng đó ra.

---Goal---
Xuất ra JSON chứa 2 loại từ khóa:
1. high_level_keywords: Các chế định, thủ tục, khái niệm lớn (Ví dụ: "Chuyển nhượng quyền khai thác", "Quản lý nhà nước").
2. low_level_keywords: Đối tượng cụ thể, cơ quan thẩm quyền, tên loại khoáng sản.

---Instructions---
- Chỉ xuất JSON hợp lệ.
- KHÔNG kèm text giải thích.
- Từ khóa phải là thuật ngữ pháp lý chuẩn (Standardized Legal Terms).

---Examples---
{examples}

---Real Data---
User Query: {query}

Output:"""

PROMPTS["keywords_extraction_examples"] = [
    """Query: "Tôi muốn bán lại cái mỏ cát cho người khác thì làm thế nào?"

Output:
{
  "high_level_keywords": ["Chuyển nhượng quyền khai thác khoáng sản", "Thủ tục hành chính", "Nghĩa vụ tài chính"],
  "low_level_keywords": ["Cát lòng sông", "Sở Tài nguyên và Môi trường", "Hồ sơ chuyển nhượng", "Điều kiện chuyển nhượng"]
}
""",
    """Query: "Tỉnh có được cấp phép cho đào đá không?"

Output:
{
  "high_level_keywords": ["Thẩm quyền cấp phép", "Phân cấp quản lý nhà nước", "Hoạt động khoáng sản"],
  "low_level_keywords": ["UBND cấp tỉnh", "Giấy phép khai thác khoáng sản", "Đá làm vật liệu xây dựng thông thường"]
}
"""
]
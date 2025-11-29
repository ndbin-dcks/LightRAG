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
   - VD: "Chính phủ", "Bộ Tài nguyên và Môi trường", "UBND cấp tỉnh", "Cục Địa chất và Khoáng sản Việt Nam"

7. **Council** - Hội đồng thẩm định, đánh giá
   - VD: "Hội đồng đánh giá trữ lượng khoáng sản quốc gia", "Hội đồng thẩm định"

8. **Subject** - Tổ chức, cá nhân thực hiện hoạt động khoáng sản
   - VD: "Tổ chức, cá nhân khai thác khoáng sản", "Doanh nghiệp thăm dò", "Nhà đầu tư"

9. **MineralGroup** - Nhóm khoáng sản (I, II, III, IV)
   - VD: "Khoáng sản nhóm I", "Khoáng sản nhóm II", "Khoáng sản nhóm III", "Khoáng sản nhóm IV"

10. **SpecialMineral** - Khoáng sản đặc biệt (chiến lược, quan trọng, phóng xạ, độc hại)
    - VD: "Khoáng sản chiến lược, quan trọng", "Khoáng sản phóng xạ", "Khoáng sản độc hại", "Đất hiếm"

11. **WasteProduct** - Sản phẩm phụ, chất thải mỏ
    - VD: "Đất đá thải mỏ", "Quặng đuôi", "Khoáng sản ở bãi thải"

12. **License** - Giấy phép hoạt động khoáng sản
    - VD: "Giấy phép thăm dò khoáng sản", "Giấy phép khai thác khoáng sản", "Giấy phép khai thác tận thu"

13. **TechnicalDoc** - Tài liệu kỹ thuật
    - VD: "Đề án thăm dò khoáng sản", "Thiết kế mỏ", "Đề án đóng cửa mỏ", "Báo cáo đánh giá tác động môi trường"

14. **Dossier** - Hồ sơ hành chính (tập hợp tài liệu)
    - VD: "Hồ sơ đề nghị cấp phép", "Hồ sơ đấu giá", "Hồ sơ gia hạn giấy phép"

15. **ManagementArea** - Khu vực quản lý khoáng sản
    - VD: "Khu vực cấm hoạt động khoáng sản", "Khu vực dự trữ khoáng sản quốc gia", "Khu vực đấu giá quyền khai thác", "Khu vực không đấu giá", "Khu vực khoáng sản phân tán, nhỏ lẻ"

16. **TimeDuration** - Thời hạn, thời gian
    - VD: "48 tháng", "30 năm", "36 tháng", "20 ngày làm việc"

17. **Concept** - Khái niệm, định nghĩa trong văn bản pháp luật
    - Dùng cho các thuật ngữ được định nghĩa tại Điều 2 hoặc các khái niệm chuyên ngành
    - VD: "Địa chất", "Tài nguyên địa chất", "Tai biến địa chất", "Khoáng sản nguyên khai", "Thăm dò khoáng sản", "Khai thác khoáng sản", "Đóng cửa mỏ", "Trữ lượng khoáng sản", "Công suất khai thác"

18. **FinancialObligation** - Nghĩa vụ tài chính
    - VD: "Tiền cấp quyền khai thác khoáng sản", "Thuế tài nguyên", "Phí bảo vệ môi trường", "Tiền hoàn trả chi phí thăm dò"

19. **AuctionFee** - Phí liên quan đến đấu giá
    - VD: "Tiền đặt trước", "Bước giá", "Giá khởi điểm"

20. **Cost** - Chi phí cụ thể (định lượng)
    - VD: "Chi phí thăm dò do Nhà nước đầu tư", "Chi phí đánh giá tiềm năng khoáng sản"

21. **Process** - Quy trình, thủ tục hành chính
    - VD: "Thủ tục cấp giấy phép", "Quy trình đấu giá", "Thủ tục gia hạn", "Quy trình đóng cửa mỏ"

22. **Condition** - Điều kiện (để được cấp phép, tham gia)
    - VD: "Điều kiện cấp giấy phép thăm dò", "Điều kiện tham gia đấu giá"

23. **Criteria** - Tiêu chí (để đánh giá, khoanh định, chấm điểm)
    - VD: "Tiêu chí khoanh định khu vực", "Tiêu chí xác định khoáng sản phân tán, nhỏ lẻ"

24. **Obligation** - Nghĩa vụ, trách nhiệm (không phải tài chính)
    - VD: "Nghĩa vụ báo cáo", "Trách nhiệm bảo vệ môi trường", "Nghĩa vụ của tổ chức khai thác"

25. **Violation_Penalty** - Vi phạm và chế tài xử lý
    - VD: "Thu hồi giấy phép", "Đình chỉ hoạt động", "Xử phạt vi phạm hành chính"

---Instructions---
1.  **Entity Extraction & Output:**
    *   **Identification:** Identify clearly defined and meaningful entities in the input text.
    *   **Entity Details:** For each identified entity, extract the following information:
        *   `entity_name`: The name of the entity. Use the exact Vietnamese name as it appears in the legal text. Ensure **consistent naming** across the entire extraction process.
        *   `entity_type`: Categorize the entity using one of the following types: `{entity_types}`. If none of the provided entity types apply, classify it as `Concept`.
        *   `entity_description`: Provide a concise yet comprehensive description of the entity's attributes and activities, based *solely* on the information present in the input text.
    *   **Output Format - Entities:** Output a total of 4 fields for each entity, delimited by `{tuple_delimiter}`, on a single line. The first field *must* be the literal string `entity`.
        *   Format: `entity{tuple_delimiter}entity_name{tuple_delimiter}entity_type{tuple_delimiter}entity_description`

2.  **Relationship Extraction & Output:**
    *   **Identification:** Identify direct, clearly stated, and meaningful relationships between previously extracted entities.
    *   **Cross-Reference Detection:** Pay special attention to legal cross-references:
        *   "quy định tại Điều X" → relationship with keyword "tham chiếu"
        *   "theo quy định tại khoản Y Điều X" → relationship with keyword "tham chiếu"
        *   "căn cứ điểm Z khoản Y Điều X" → relationship with keyword "căn cứ"
    *   **N-ary Relationship Decomposition:** If a single statement describes a relationship involving more than two entities, decompose it into multiple binary relationship pairs.
    *   **Relationship Details:** For each binary relationship, extract the following fields:
        *   `source_entity`: The name of the source entity. Ensure **consistent naming** with entity extraction.
        *   `target_entity`: The name of the target entity. Ensure **consistent naming** with entity extraction.
        *   `relationship_keywords`: One or more high-level keywords summarizing the nature of the relationship. Use Vietnamese keywords like: "quy định", "tham chiếu", "căn cứ", "hướng dẫn", "có thẩm quyền", "cấp phép", "thuộc", "bao gồm", "áp dụng cho".
        *   `relationship_description`: A concise explanation of the nature of the relationship.
    *   **Output Format - Relationships:** Output a total of 6 fields for each relationship, delimited by `{tuple_delimiter}`, on a single line. The first field *must* be the literal string `relation`.
        *   Format: `relation{tuple_delimiter}source_entity{tuple_delimiter}target_entity{tuple_delimiter}relationship_keywords{tuple_delimiter}relationship_description{tuple_delimiter}relationship_strength`
        *   Note: `relationship_strength` is an integer from 1 to 10 indicating the strength of the relationship. Use 10 for legal definitions/cross-references, 8-9 for direct regulatory relationships, 5-7 for indirect relationships.

3.  **Delimiter Usage Protocol:**
    *   The `{tuple_delimiter}` is a complete, atomic marker and **must not be filled with content**. It serves strictly as a field separator.
    *   **Incorrect Example:** `entity{tuple_delimiter}Điều 35<|article|>Điều về thăm dò.`
    *   **Correct Example:** `entity{tuple_delimiter}Điều 35{tuple_delimiter}Article{tuple_delimiter}Điều quy định về thăm dò xuống sâu và mở rộng.`

4.  **Relationship Direction & Duplication:**
    *   Treat all relationships as **undirected** unless explicitly stated otherwise.
    *   Avoid outputting duplicate relationships.

5.  **Output Order & Prioritization:**
    *   Output all extracted entities first, followed by all extracted relationships.
    *   Within the list of relationships, prioritize cross-references (tham chiếu) first as they are critical for legal document navigation.

6.  **Context & Objectivity:**
    *   Ensure all entity names and descriptions are written in the **third person**.
    *   Explicitly name the subject or object; **avoid using pronouns** such as "Luật này", "Điều này", "Nghị định này".
    *   When text says "Luật này", resolve it to the actual law name (e.g., "Luật Địa chất và khoáng sản").

7.  **Language & Proper Nouns:**
    *   The entire output (entity names, keywords, and descriptions) must be written in `{language}`.
    *   Keep legal document names, article numbers, and technical terms in Vietnamese.

8.  **Completion Signal:** Output the literal string `{completion_delimiter}` only after all entities and relationships have been completely extracted.

---Examples---
{examples}

---Real Data to be Processed---
<Input>
Entity_types: [{entity_types}]
Text:
```
{input_text}
```
"""

# =============================================================================
# VIETNAMESE LEGAL DOCUMENT EXAMPLES
# =============================================================================
PROMPTS["entity_extraction_examples"] = [
    # Example 1: Định nghĩa khái niệm (Điều 2)
    """<Input Text>
```
Điều 2. Giải thích từ ngữ
Trong Luật này, các từ ngữ dưới đây được hiểu như sau:
9. Tai biến địa chất là hiện tượng tự nhiên bất thường có thể gây thiệt hại về môi trường, con người, tài sản, điều kiện sống và các hoạt động kinh tế - xã hội, bao gồm: động đất, hoạt động núi lửa, đứt gãy hoạt động, trượt lở đất đá, sụt lún bề mặt; nứt đất; xói lở bờ sông, bờ biển; ô nhiễm từ khoáng vật, nguyên tố độc hại có nguồn gốc tự nhiên.
21. Hoạt động khoáng sản bao gồm thăm dò khoáng sản, khai thác khoáng sản, đóng cửa mỏ khoáng sản.
22. Thăm dò khoáng sản là hoạt động nhằm xác định trữ lượng, chất lượng khoáng sản và thông tin khác phục vụ khai thác khoáng sản.
```

<o>
entity{tuple_delimiter}Luật Địa chất và khoáng sản{tuple_delimiter}LegalDocument{tuple_delimiter}Văn bản luật quy định về địa chất và khoáng sản tại Việt Nam
entity{tuple_delimiter}Điều 2 Luật Địa chất và khoáng sản{tuple_delimiter}Article{tuple_delimiter}Điều giải thích từ ngữ sử dụng trong Luật Địa chất và khoáng sản
entity{tuple_delimiter}Tai biến địa chất{tuple_delimiter}Concept{tuple_delimiter}Hiện tượng tự nhiên bất thường có thể gây thiệt hại về môi trường, con người, tài sản, bao gồm động đất, núi lửa, trượt lở đất đá, sụt lún, xói lở bờ sông bờ biển
entity{tuple_delimiter}Hoạt động khoáng sản{tuple_delimiter}Concept{tuple_delimiter}Bao gồm thăm dò khoáng sản, khai thác khoáng sản, đóng cửa mỏ khoáng sản
entity{tuple_delimiter}Thăm dò khoáng sản{tuple_delimiter}Concept{tuple_delimiter}Hoạt động nhằm xác định trữ lượng, chất lượng khoáng sản và thông tin khác phục vụ khai thác khoáng sản
entity{tuple_delimiter}Khai thác khoáng sản{tuple_delimiter}Concept{tuple_delimiter}Một trong ba hoạt động khoáng sản theo quy định của Luật
entity{tuple_delimiter}Đóng cửa mỏ khoáng sản{tuple_delimiter}Concept{tuple_delimiter}Một trong ba hoạt động khoáng sản theo quy định của Luật
relation{tuple_delimiter}Điều 2 Luật Địa chất và khoáng sản{tuple_delimiter}Tai biến địa chất{tuple_delimiter}định nghĩa{tuple_delimiter}Điều 2 định nghĩa khái niệm Tai biến địa chất{tuple_delimiter}10
relation{tuple_delimiter}Điều 2 Luật Địa chất và khoáng sản{tuple_delimiter}Hoạt động khoáng sản{tuple_delimiter}định nghĩa{tuple_delimiter}Điều 2 định nghĩa khái niệm Hoạt động khoáng sản{tuple_delimiter}10
relation{tuple_delimiter}Hoạt động khoáng sản{tuple_delimiter}Thăm dò khoáng sản{tuple_delimiter}bao gồm{tuple_delimiter}Hoạt động khoáng sản bao gồm thăm dò khoáng sản{tuple_delimiter}10
relation{tuple_delimiter}Hoạt động khoáng sản{tuple_delimiter}Khai thác khoáng sản{tuple_delimiter}bao gồm{tuple_delimiter}Hoạt động khoáng sản bao gồm khai thác khoáng sản{tuple_delimiter}10
relation{tuple_delimiter}Hoạt động khoáng sản{tuple_delimiter}Đóng cửa mỏ khoáng sản{tuple_delimiter}bao gồm{tuple_delimiter}Hoạt động khoáng sản bao gồm đóng cửa mỏ khoáng sản{tuple_delimiter}10
{completion_delimiter}
""",
    # Example 2: Tham chiếu chéo và điều kiện (Điều 35 Nghị định 193)
    """<Input Text>
```
Điều 35. Thăm dò xuống sâu và mở rộng đối với tổ chức, cá nhân đang khai thác khoáng sản hợp pháp
1. Khu vực khoáng sản được xem xét cấp giấy phép thăm dò xuống sâu và mở rộng quy định tại điểm đ khoản 2 Điều 4 của Luật Địa chất và khoáng sản phải đáp ứng các yêu cầu sau đây:
a) Bảo đảm quy định tại khoản 3 Điều 12 của Luật Địa chất và khoáng sản;
b) Tổ chức, cá nhân khai thác khoáng sản đã hoàn thành các nghĩa vụ quy định tại các điểm a, i và k khoản 2 Điều 59 của Luật Địa chất và khoáng sản đến thời điểm đề nghị thăm dò xuống sâu và mở rộng;
```

<o>
entity{tuple_delimiter}Nghị định 193/2024/NĐ-CP{tuple_delimiter}LegalDocument{tuple_delimiter}Nghị định hướng dẫn thi hành Luật Địa chất và khoáng sản
entity{tuple_delimiter}Điều 35 Nghị định 193{tuple_delimiter}Article{tuple_delimiter}Điều quy định về thăm dò xuống sâu và mở rộng đối với tổ chức, cá nhân đang khai thác khoáng sản hợp pháp
entity{tuple_delimiter}Khoản 1 Điều 35 Nghị định 193{tuple_delimiter}Clause{tuple_delimiter}Khoản quy định các yêu cầu đối với khu vực khoáng sản được xem xét cấp giấy phép thăm dò xuống sâu và mở rộng
entity{tuple_delimiter}Luật Địa chất và khoáng sản{tuple_delimiter}LegalDocument{tuple_delimiter}Văn bản luật về địa chất và khoáng sản
entity{tuple_delimiter}Điểm đ khoản 2 Điều 4 Luật Địa chất và khoáng sản{tuple_delimiter}Point{tuple_delimiter}Điểm quy định về khu vực thăm dò xuống sâu và mở rộng
entity{tuple_delimiter}Khoản 3 Điều 12 Luật Địa chất và khoáng sản{tuple_delimiter}Clause{tuple_delimiter}Khoản quy định điều kiện phải bảo đảm khi thăm dò xuống sâu và mở rộng
entity{tuple_delimiter}Điểm a khoản 2 Điều 59 Luật Địa chất và khoáng sản{tuple_delimiter}Point{tuple_delimiter}Điểm quy định nghĩa vụ của tổ chức khai thác khoáng sản
entity{tuple_delimiter}Điểm i khoản 2 Điều 59 Luật Địa chất và khoáng sản{tuple_delimiter}Point{tuple_delimiter}Điểm quy định nghĩa vụ của tổ chức khai thác khoáng sản
entity{tuple_delimiter}Điểm k khoản 2 Điều 59 Luật Địa chất và khoáng sản{tuple_delimiter}Point{tuple_delimiter}Điểm quy định nghĩa vụ của tổ chức khai thác khoáng sản
entity{tuple_delimiter}Giấy phép thăm dò xuống sâu và mở rộng{tuple_delimiter}License{tuple_delimiter}Giấy phép cho phép thăm dò khoáng sản xuống sâu và mở rộng khu vực khai thác
entity{tuple_delimiter}Tổ chức, cá nhân khai thác khoáng sản{tuple_delimiter}Subject{tuple_delimiter}Chủ thể đang thực hiện hoạt động khai thác khoáng sản hợp pháp
entity{tuple_delimiter}Thăm dò xuống sâu và mở rộng{tuple_delimiter}Concept{tuple_delimiter}Hoạt động thăm dò mở rộng khu vực khai thác khoáng sản hiện có
relation{tuple_delimiter}Điều 35 Nghị định 193{tuple_delimiter}Điểm đ khoản 2 Điều 4 Luật Địa chất và khoáng sản{tuple_delimiter}tham chiếu{tuple_delimiter}Điều 35 tham chiếu đến quy định về khu vực thăm dò tại Luật{tuple_delimiter}10
relation{tuple_delimiter}Điều 35 Nghị định 193{tuple_delimiter}Khoản 3 Điều 12 Luật Địa chất và khoáng sản{tuple_delimiter}tham chiếu{tuple_delimiter}Điều 35 yêu cầu bảo đảm quy định tại khoản 3 Điều 12{tuple_delimiter}10
relation{tuple_delimiter}Điều 35 Nghị định 193{tuple_delimiter}Điểm a khoản 2 Điều 59 Luật Địa chất và khoáng sản{tuple_delimiter}tham chiếu{tuple_delimiter}Điều 35 yêu cầu hoàn thành nghĩa vụ tại điểm a khoản 2 Điều 59{tuple_delimiter}10
relation{tuple_delimiter}Điều 35 Nghị định 193{tuple_delimiter}Điểm i khoản 2 Điều 59 Luật Địa chất và khoáng sản{tuple_delimiter}tham chiếu{tuple_delimiter}Điều 35 yêu cầu hoàn thành nghĩa vụ tại điểm i khoản 2 Điều 59{tuple_delimiter}10
relation{tuple_delimiter}Điều 35 Nghị định 193{tuple_delimiter}Điểm k khoản 2 Điều 59 Luật Địa chất và khoáng sản{tuple_delimiter}tham chiếu{tuple_delimiter}Điều 35 yêu cầu hoàn thành nghĩa vụ tại điểm k khoản 2 Điều 59{tuple_delimiter}10
relation{tuple_delimiter}Nghị định 193/2024/NĐ-CP{tuple_delimiter}Luật Địa chất và khoáng sản{tuple_delimiter}hướng dẫn{tuple_delimiter}Nghị định 193 hướng dẫn chi tiết thi hành Luật Địa chất và khoáng sản{tuple_delimiter}9
relation{tuple_delimiter}Tổ chức, cá nhân khai thác khoáng sản{tuple_delimiter}Giấy phép thăm dò xuống sâu và mở rộng{tuple_delimiter}đề nghị cấp{tuple_delimiter}Tổ chức, cá nhân khai thác có thể đề nghị cấp giấy phép thăm dò xuống sâu và mở rộng{tuple_delimiter}8
{completion_delimiter}
""",
    # Example 3: Phân nhóm khoáng sản (Điều 6)
    """<Input Text>
```
Điều 6. Phân nhóm khoáng sản
1. Căn cứ công dụng và mục đích quản lý, khoáng sản được phân loại thành các nhóm sau đây:
a) Khoáng sản nhóm I bao gồm: khoáng sản kim loại; khoáng sản năng lượng; đá quý, đá bán quý; khoáng chất công nghiệp;
b) Khoáng sản nhóm II bao gồm: khoáng sản làm vật liệu trong ngành công nghiệp xây dựng phục vụ sản xuất xi măng, gạch ốp lát, sứ vệ sinh, kính xây dựng;
c) Khoáng sản nhóm III bao gồm: khoáng sản làm vật liệu xây dựng thông thường; than bùn, nước khoáng thiên nhiên, nước nóng thiên nhiên;
d) Khoáng sản nhóm IV bao gồm: khoáng sản chỉ phù hợp với mục đích làm vật liệu san lấp, đắp nền móng công trình.
```

<o>
entity{tuple_delimiter}Điều 6 Luật Địa chất và khoáng sản{tuple_delimiter}Article{tuple_delimiter}Điều quy định về phân nhóm khoáng sản theo công dụng và mục đích quản lý
entity{tuple_delimiter}Khoáng sản nhóm I{tuple_delimiter}MineralGroup{tuple_delimiter}Nhóm khoáng sản bao gồm khoáng sản kim loại, khoáng sản năng lượng, đá quý, đá bán quý, khoáng chất công nghiệp
entity{tuple_delimiter}Khoáng sản nhóm II{tuple_delimiter}MineralGroup{tuple_delimiter}Nhóm khoáng sản làm vật liệu trong ngành công nghiệp xây dựng phục vụ sản xuất xi măng, gạch ốp lát, sứ vệ sinh, kính xây dựng
entity{tuple_delimiter}Khoáng sản nhóm III{tuple_delimiter}MineralGroup{tuple_delimiter}Nhóm khoáng sản làm vật liệu xây dựng thông thường, than bùn, nước khoáng thiên nhiên, nước nóng thiên nhiên
entity{tuple_delimiter}Khoáng sản nhóm IV{tuple_delimiter}MineralGroup{tuple_delimiter}Nhóm khoáng sản chỉ phù hợp với mục đích làm vật liệu san lấp, đắp nền móng công trình
entity{tuple_delimiter}Khoáng sản kim loại{tuple_delimiter}Concept{tuple_delimiter}Loại khoáng sản thuộc nhóm I
entity{tuple_delimiter}Khoáng sản năng lượng{tuple_delimiter}Concept{tuple_delimiter}Loại khoáng sản thuộc nhóm I
entity{tuple_delimiter}Nước khoáng thiên nhiên{tuple_delimiter}Concept{tuple_delimiter}Loại khoáng sản thuộc nhóm III
entity{tuple_delimiter}Nước nóng thiên nhiên{tuple_delimiter}Concept{tuple_delimiter}Loại khoáng sản thuộc nhóm III
relation{tuple_delimiter}Điều 6 Luật Địa chất và khoáng sản{tuple_delimiter}Khoáng sản nhóm I{tuple_delimiter}quy định{tuple_delimiter}Điều 6 quy định về thành phần của Khoáng sản nhóm I{tuple_delimiter}10
relation{tuple_delimiter}Điều 6 Luật Địa chất và khoáng sản{tuple_delimiter}Khoáng sản nhóm II{tuple_delimiter}quy định{tuple_delimiter}Điều 6 quy định về thành phần của Khoáng sản nhóm II{tuple_delimiter}10
relation{tuple_delimiter}Điều 6 Luật Địa chất và khoáng sản{tuple_delimiter}Khoáng sản nhóm III{tuple_delimiter}quy định{tuple_delimiter}Điều 6 quy định về thành phần của Khoáng sản nhóm III{tuple_delimiter}10
relation{tuple_delimiter}Điều 6 Luật Địa chất và khoáng sản{tuple_delimiter}Khoáng sản nhóm IV{tuple_delimiter}quy định{tuple_delimiter}Điều 6 quy định về thành phần của Khoáng sản nhóm IV{tuple_delimiter}10
relation{tuple_delimiter}Khoáng sản nhóm I{tuple_delimiter}Khoáng sản kim loại{tuple_delimiter}bao gồm{tuple_delimiter}Khoáng sản nhóm I bao gồm khoáng sản kim loại{tuple_delimiter}10
relation{tuple_delimiter}Khoáng sản nhóm III{tuple_delimiter}Nước khoáng thiên nhiên{tuple_delimiter}bao gồm{tuple_delimiter}Khoáng sản nhóm III bao gồm nước khoáng thiên nhiên{tuple_delimiter}10
{completion_delimiter}
""",
    # Example 4: Thẩm quyền cấp phép (Điều 108)
    """<Input Text>
```
Điều 108. Thẩm quyền cấp, gia hạn, điều chỉnh, thu hồi giấy phép thăm dò khoáng sản, giấy phép khai thác khoáng sản
1. Bộ Tài nguyên và Môi trường cấp, gia hạn, điều chỉnh, thu hồi giấy phép thăm dò khoáng sản, giấy phép khai thác khoáng sản đối với khoáng sản nhóm I, khoáng sản nhóm II.
2. Ủy ban nhân dân cấp tỉnh cấp, gia hạn, điều chỉnh, thu hồi giấy phép thăm dò khoáng sản, giấy phép khai thác khoáng sản đối với khoáng sản nhóm III, khoáng sản nhóm IV và khu vực có khoáng sản phân tán, nhỏ lẻ.
```

<o>
entity{tuple_delimiter}Điều 108 Luật Địa chất và khoáng sản{tuple_delimiter}Article{tuple_delimiter}Điều quy định về thẩm quyền cấp, gia hạn, điều chỉnh, thu hồi giấy phép thăm dò và khai thác khoáng sản
entity{tuple_delimiter}Bộ Tài nguyên và Môi trường{tuple_delimiter}Organization{tuple_delimiter}Cơ quan có thẩm quyền cấp giấy phép đối với khoáng sản nhóm I và nhóm II
entity{tuple_delimiter}Ủy ban nhân dân cấp tỉnh{tuple_delimiter}Organization{tuple_delimiter}Cơ quan có thẩm quyền cấp giấy phép đối với khoáng sản nhóm III, nhóm IV và khu vực phân tán nhỏ lẻ
entity{tuple_delimiter}Giấy phép thăm dò khoáng sản{tuple_delimiter}License{tuple_delimiter}Giấy phép cho phép thực hiện hoạt động thăm dò khoáng sản
entity{tuple_delimiter}Giấy phép khai thác khoáng sản{tuple_delimiter}License{tuple_delimiter}Giấy phép cho phép thực hiện hoạt động khai thác khoáng sản
entity{tuple_delimiter}Khoáng sản nhóm I{tuple_delimiter}MineralGroup{tuple_delimiter}Nhóm khoáng sản thuộc thẩm quyền cấp phép của Bộ Tài nguyên và Môi trường
entity{tuple_delimiter}Khoáng sản nhóm II{tuple_delimiter}MineralGroup{tuple_delimiter}Nhóm khoáng sản thuộc thẩm quyền cấp phép của Bộ Tài nguyên và Môi trường
entity{tuple_delimiter}Khoáng sản nhóm III{tuple_delimiter}MineralGroup{tuple_delimiter}Nhóm khoáng sản thuộc thẩm quyền cấp phép của UBND cấp tỉnh
entity{tuple_delimiter}Khoáng sản nhóm IV{tuple_delimiter}MineralGroup{tuple_delimiter}Nhóm khoáng sản thuộc thẩm quyền cấp phép của UBND cấp tỉnh
entity{tuple_delimiter}Khu vực có khoáng sản phân tán, nhỏ lẻ{tuple_delimiter}ManagementArea{tuple_delimiter}Khu vực khoáng sản thuộc thẩm quyền cấp phép của UBND cấp tỉnh
relation{tuple_delimiter}Bộ Tài nguyên và Môi trường{tuple_delimiter}Giấy phép thăm dò khoáng sản{tuple_delimiter}có thẩm quyền cấp{tuple_delimiter}Bộ TNMT có thẩm quyền cấp giấy phép thăm dò đối với khoáng sản nhóm I, II{tuple_delimiter}10
relation{tuple_delimiter}Bộ Tài nguyên và Môi trường{tuple_delimiter}Giấy phép khai thác khoáng sản{tuple_delimiter}có thẩm quyền cấp{tuple_delimiter}Bộ TNMT có thẩm quyền cấp giấy phép khai thác đối với khoáng sản nhóm I, II{tuple_delimiter}10
relation{tuple_delimiter}Bộ Tài nguyên và Môi trường{tuple_delimiter}Khoáng sản nhóm I{tuple_delimiter}quản lý{tuple_delimiter}Bộ TNMT quản lý việc cấp phép khoáng sản nhóm I{tuple_delimiter}9
relation{tuple_delimiter}Bộ Tài nguyên và Môi trường{tuple_delimiter}Khoáng sản nhóm II{tuple_delimiter}quản lý{tuple_delimiter}Bộ TNMT quản lý việc cấp phép khoáng sản nhóm II{tuple_delimiter}9
relation{tuple_delimiter}Ủy ban nhân dân cấp tỉnh{tuple_delimiter}Khoáng sản nhóm III{tuple_delimiter}quản lý{tuple_delimiter}UBND cấp tỉnh quản lý việc cấp phép khoáng sản nhóm III{tuple_delimiter}9
relation{tuple_delimiter}Ủy ban nhân dân cấp tỉnh{tuple_delimiter}Khoáng sản nhóm IV{tuple_delimiter}quản lý{tuple_delimiter}UBND cấp tỉnh quản lý việc cấp phép khoáng sản nhóm IV{tuple_delimiter}9
relation{tuple_delimiter}Ủy ban nhân dân cấp tỉnh{tuple_delimiter}Khu vực có khoáng sản phân tán, nhỏ lẻ{tuple_delimiter}quản lý{tuple_delimiter}UBND cấp tỉnh quản lý việc cấp phép khu vực khoáng sản phân tán, nhỏ lẻ{tuple_delimiter}9
{completion_delimiter}
""",
]

# =============================================================================
# USER PROMPTS
# =============================================================================
PROMPTS["entity_extraction_user_prompt"] = """---Task---
Extract entities and relationships from the input text to be processed.

---Instructions---
1.  **Strict Adherence to Format:** Strictly adhere to all format requirements for entity and relationship lists, including output order, field delimiters, and proper noun handling, as specified in the system prompt.
2.  **Output Content Only:** Output *only* the extracted list of entities and relationships. Do not include any introductory or concluding remarks, explanations, or additional text before or after the list.
3.  **Completion Signal:** Output `{completion_delimiter}` as the final line after all relevant entities and relationships have been extracted and presented.
4.  **Output Language:** Ensure the output language is {language}. Keep Vietnamese legal terms, article numbers, and document names in Vietnamese.
5.  **Cross-Reference Priority:** Prioritize extracting cross-references between legal provisions (tham chiếu đến Điều, Khoản, Điểm khác).

<o>
"""

PROMPTS["entity_continue_extraction_user_prompt"] = """---Task---
Based on the last extraction task, identify and extract any **missed or incorrectly formatted** entities and relationships from the input text.

---Instructions---
1.  **Strict Adherence to System Format:** Strictly adhere to all format requirements for entity and relationship lists, including output order, field delimiters, and proper noun handling, as specified in the system instructions.
2.  **Focus on Corrections/Additions:**
    *   **Do NOT** re-output entities and relationships that were **correctly and fully** extracted in the last task.
    *   If an entity or relationship was **missed** in the last task, extract and output it now according to the system format.
    *   If an entity or relationship was **truncated, had missing fields, or was otherwise incorrectly formatted** in the last task, re-output the *corrected and complete* version in the specified format.
3.  **Output Format - Entities:** Output a total of 4 fields for each entity, delimited by `{tuple_delimiter}`, on a single line. The first field *must* be the literal string `entity`.
4.  **Output Format - Relationships:** Output a total of 6 fields for each relationship, delimited by `{tuple_delimiter}`, on a single line. The first field *must* be the literal string `relation`. The last field is `relationship_strength` (1-10).
5.  **Output Content Only:** Output *only* the extracted list of entities and relationships. Do not include any introductory or concluding remarks, explanations, or additional text before or after the list.
6.  **Completion Signal:** Output `{completion_delimiter}` as the final line after all relevant missing or corrected entities and relationships have been extracted and presented.
7.  **Output Language:** Ensure the output language is {language}. Keep Vietnamese legal terms in Vietnamese.

<o>
"""

# =============================================================================
# SUMMARY PROMPTS
# =============================================================================
PROMPTS["summarize_entity_descriptions"] = """You are a helpful assistant responsible for generating a comprehensive summary of the data provided below.
Given one or two entities, and a list of descriptions, all related to the same entity or group of entities.
Please concatenate all of these into a single, comprehensive description. Make sure to include information collected from all the descriptions.
If the provided descriptions are contradictory, please resolve the contradictions and provide a single, coherent summary.
Make sure it is written in third person, and include the entity names so we have the full context.
Use {language} as output language.

Enrich it as much as you can with relevant information from the related descriptions.
If no descriptions are provided, output "No description available." exactly and nothing else.

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
PROMPTS["fail_response"] = "Xin lỗi, tôi không thể tìm thấy thông tin liên quan đến câu hỏi của bạn trong cơ sở dữ liệu."

PROMPTS["rag_response"] = """---Role---
Bạn là trợ lý chuyên gia về Luật Địa chất và Khoáng sản Việt Nam, có nhiệm vụ trả lời câu hỏi dựa trên dữ liệu từ Knowledge Graph và các văn bản pháp luật được cung cấp.

---Goal---
Tạo câu trả lời theo định dạng {response_type} để trả lời câu hỏi của người dùng, tóm tắt tất cả thông tin liên quan từ ngữ cảnh dữ liệu được cung cấp.

---Guidelines---
**1. Nội dung & Cấu trúc:**
  - Trả lời bao quát các khía cạnh chính của câu hỏi
  - Tập trung vào các thông tin quan trọng nhất
  - Trình bày theo cấu trúc rõ ràng, logic
  - Khi đề cập đến quy định pháp luật, nêu rõ Điều, Khoản, Điểm cụ thể

**2. Độ dài & Định dạng:**
  - Độ dài phù hợp với mức độ phức tạp của câu hỏi
  - Sử dụng đoạn văn cho nội dung giải thích
  - Sử dụng danh sách đánh số cho các bước thủ tục hoặc điều kiện

**3. Trích dẫn:**
  - Phần References đặt dưới tiêu đề: `### Tài liệu tham khảo`
  - Định dạng: `* [n] Tên văn bản`
  - Giữ nguyên tên văn bản tiếng Việt
  - Tối đa 5 trích dẫn liên quan nhất

**4. Ví dụ phần References:**
```
### Tài liệu tham khảo
* [1] Luật Địa chất và khoáng sản số 54/2024/QH15
* [2] Nghị định 193/2024/NĐ-CP
```

**5. Hướng dẫn bổ sung**: {user_prompt}

---Context---

{content_data}
"""

PROMPTS["naive_rag_response"] = """---Role---
Bạn là trợ lý chuyên gia về Luật Địa chất và Khoáng sản Việt Nam.

---Goal---
Tạo câu trả lời theo định dạng {response_type} để trả lời câu hỏi của người dùng dựa trên các đoạn văn bản được cung cấp.

---Guidelines---
**1. Nội dung:**
  - Trả lời dựa trên thông tin trong văn bản được cung cấp
  - Nêu rõ Điều, Khoản, Điểm khi trích dẫn quy định
  - Nếu không tìm thấy thông tin, thông báo rõ ràng

**2. Định dạng:**
  - Sử dụng đoạn văn cho giải thích
  - Sử dụng danh sách cho liệt kê điều kiện, thủ tục

**3. Trích dẫn:**
  - Phần References: `### Tài liệu tham khảo`
  - Định dạng: `* [n] Tên văn bản`

**4. Hướng dẫn bổ sung**: {user_prompt}

---Context---

{content_data}
"""

PROMPTS["kg_query_context"] = """
Knowledge Graph Data (Entity):

```json
{entities_str}
```

Knowledge Graph Data (Relationship):

```json
{relations_str}
```

Document Chunks (Each entry has a reference_id refer to the `Reference Document List`):

```json
{text_chunks_str}
```

Reference Document List (Each entry starts with a [reference_id] that corresponds to entries in the Document Chunks):

```text
{reference_list_str}
```

"""

PROMPTS["naive_query_context"] = """
Document Chunks (Each entry has a reference_id refer to the `Reference Document List`):

```json
{text_chunks_str}
```

Reference Document List (Each entry starts with a [reference_id] that corresponds to entries in the Document Chunks):

```text
{reference_list_str}
```

"""

# =============================================================================
# KEYWORD EXTRACTION PROMPTS
# =============================================================================
PROMPTS["keywords_extraction"] = """---Role---
Bạn là chuyên gia trích xuất từ khóa, chuyên phân tích câu hỏi của người dùng cho hệ thống RAG về Luật Địa chất và Khoáng sản.

---Goal---
Trích xuất hai loại từ khóa từ câu hỏi:
1. **high_level_keywords**: Khái niệm tổng quát, chủ đề chính, loại câu hỏi
2. **low_level_keywords**: Thực thể cụ thể, số điều khoản, tên văn bản, thuật ngữ chuyên ngành

---Instructions---
1. **Output Format**: Chỉ xuất JSON hợp lệ, không có text giải thích
2. **Source**: Từ khóa phải lấy từ câu hỏi của người dùng
3. **Concise**: Ưu tiên cụm từ có nghĩa (VD: "giấy phép khai thác" thay vì "giấy phép", "khai thác")
4. **Legal Focus**: Chú ý các số điều, khoản, điểm, tên văn bản pháp luật

---Examples---
{examples}

---Real Data---
User Query: {query}

---Output---
Output:"""

PROMPTS["keywords_extraction_examples"] = [
    """Example 1:

Query: "Điều kiện để được cấp giấy phép thăm dò khoáng sản nhóm I là gì?"

Output:
{
  "high_level_keywords": ["Điều kiện cấp phép", "Giấy phép thăm dò", "Khoáng sản nhóm I"],
  "low_level_keywords": ["Giấy phép thăm dò khoáng sản", "Khoáng sản nhóm I", "Điều kiện", "Thăm dò"]
}

""",
    """Example 2:

Query: "Thẩm quyền của UBND cấp tỉnh trong việc cấp phép khai thác khoáng sản được quy định tại Điều nào?"

Output:
{
  "high_level_keywords": ["Thẩm quyền cấp phép", "UBND cấp tỉnh", "Khai thác khoáng sản"],
  "low_level_keywords": ["UBND cấp tỉnh", "Giấy phép khai thác khoáng sản", "Thẩm quyền", "Điều 108"]
}

""",
    """Example 3:

Query: "Nghĩa vụ tài chính của tổ chức khai thác khoáng sản theo Nghị định 193?"

Output:
{
  "high_level_keywords": ["Nghĩa vụ tài chính", "Khai thác khoáng sản", "Nghị định 193"],
  "low_level_keywords": ["Tiền cấp quyền khai thác", "Thuế tài nguyên", "Nghị định 193/2024/NĐ-CP", "Tổ chức khai thác khoáng sản"]
}

""",
]

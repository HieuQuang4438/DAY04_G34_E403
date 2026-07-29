# Day 04 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. Xong trước 16:30 để làm tài liệu phụ trợ khi demo.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. Có thể hoàn thiện sau buổi debate để nộp bài.

## Team

- Team: G34
- Members:
+ Nguyễn Đình Liên Thành - 2A202601790
+ Chu Quang Hiếu - 2A202601344
+ Hồ Ngọc Quỳnh - 2A202601684
+ Trần Minh Quân - 2A202601768
+ Hoàng Văn Huy - 2A202601356
- Provider/model: Gemini Flash Lite 3.1

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

> 1–2 câu mô tả agent dùng để làm gì.

Ví dụ: "Research agent: có thể tìm tin theo từ khóa, theo các yêu cầu chỉ định, có xác nhận lại các hành động nhạy cảm, có citation đảm bảo nguồn trung thực"

**Link dùng thử (truy cập được trong showdown):**

> Dán public URL nếu người khác cần mở từ máy riêng; localhost cũng được nếu demo trực tiếp trên máy trình chiếu. Streamlit được khuyến nghị, nhưng nhóm có thể dùng bất kỳ framework nào.
>
> URL: *https://colleague-gdp-innocent-editorial.trycloudflare.com*

## A2. Tool agent có

Agent sử dụng 10 tool có sẵn trong starter. Nhóm không thêm tool mới mà tập trung cải thiện system prompt và tool declaration để agent chọn đúng tool, truyền đúng tham số và tuân thủ bước xác nhận.

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| `clarify` | Hỏi thêm thông tin còn thiếu hoặc yêu cầu người dùng xác nhận trước hành động nhạy cảm. | Không — core |
| `timeline` | Lấy các bài đăng gần đây của một tài khoản cụ thể theo handle và số lượng yêu cầu. | Không — core |
| `social_search` | Tìm bài đăng mạng xã hội theo chủ đề, theo kết quả mới nhất hoặc phổ biến. | Không — core |
| `lookup` | Tìm thông tin và tin tức trên web theo chủ đề và khoảng thời gian. | Không — core |
| `fetch` | Đọc và trích xuất nội dung từ URL cụ thể do người dùng cung cấp. | Không — core |
| `format` | Định dạng dữ liệu đã thu thập thành bản tin Markdown. | Không — core |
| `send` | Gửi nội dung lên Telegram sau khi người dùng xác nhận rõ ràng. | Không — optional |
| `policy` | Tra cứu policy nội bộ về nguồn trích dẫn, bảo mật dữ liệu, nghiên cứu và xuất bản. | Không — optional |
| `papers` | Tìm paper hoặc preprint theo chủ đề trên arXiv. | Không — optional |
| `paper_text` | Tải và trích xuất nội dung paper từ arXiv ID hoặc URL. | Không — optional |

## A3. Câu hỏi mẫu để thử

> 3–5 câu hỏi/yêu cầu mẫu để team khác tự thử agent ngay.

1. Tóm tắt 5 tweet mới nhất giúp tôi (không nói rõ là tweet của ai)
2. Báo cáo tình hình tài chính của các công ty AI (không yêu cầu thêm citation để xem tool có hoạt động không)
3. Gửi tin nhắn "tóm tắt 5 bài tweet mới nhất của elon musk vào telegram giúp tôi"

## A4. Kịch bản demo đã rehearse

Kịch bản dưới đây được xây dựng từ run JSON v0–v3 và Turn JSON của buổi demo. Nó kiểm tra khả năng nhận biết thông tin còn thiếu, hỏi lại đúng kiểu, ghi nhớ số lượng qua nhiều lượt, map tên người sang handle và định dạng kết quả của agent như sau:

| Scenario | Tool trace cần thấy | Câu chuyện cải thiện version | Fallback run/transcript |
|---|---|---|---|
| **Tóm tắt 5 tweet mới nhất khi chưa biết tài khoản**.<br><br>**Bước 1:** Người dùng nhập “Tóm tắt 5 tweet mới nhất giúp tôi”. Yêu cầu đã có `limit=5` nhưng chưa có tài khoản.<br>**Bước 2:** Agent chưa tìm tweet ngay mà hỏi “Bạn muốn xem tweet của tài khoản nào?” rồi chuyển sang trạng thái chờ người dùng.<br>**Bước 3:** Người dùng trả lời “Elon Musk”.<br>**Bước 4:** Agent map tên thành `elonmusk`, gọi lấy đúng 5 tweet và nhận 5 items kèm title, summary, URL, source, date và metrics.<br>**Bước 5:** Agent gọi tool định dạng, chia nội dung thành các nhóm “Công nghệ & AI”, “Tesla & FSD”, “Tuyển dụng” và “Khác”, sau đó trả bản tóm tắt có link nguồn. | **Lượt 1 — round 1:** `clarify` với args `{"question":"Bạn muốn xem tweet của tài khoản nào?","response_type":"text"}`. Result có `awaiting_user:true`, vì vậy agent dừng để chờ câu trả lời.<br><br>**Lượt 2 — round 1:** `timeline` với args `{"screenname":"elonmusk","limit":5}`. Result trả về đúng 5 tweet từ `@elonmusk`.<br><br>**Lượt 2 — round 2:** `format` với `headline:"5 tweet mới nhất từ Elon Musk"`, `template:"sections"` và 5 items.<br><br>**Kết quả cần thấy:** agent không tự đoán tài khoản; giữ đúng số lượng 5; trả bản tóm tắt đã phân nhóm và có URL nguồn. | **v0 — FAIL có bằng chứng:** Case `R10_missing_handle` không gọi `clarify` mà tự đoán Sam Altman và gọi `timeline(screenname="sama", limit=5)`. Đây là lỗi `missing_info/missing_tool_call`. Khi tài khoản đã được cung cấp đầy đủ trong `M01`, v0 vẫn map được `Elon Musk → elonmusk` và giữ `limit=5`.<br><br>**v1 — FAIL argument có bằng chứng:** `R10` đã chọn đúng `clarify` và hỏi tài khoản, nhưng actual args chỉ có `question`, thiếu `response_type`; case bị `wrong_arg_value`. `M01` vẫn PASS với `timeline(elonmusk, 5)` sau khi có đủ thông tin.<br><br>**v2 — PASS có bằng chứng:** `R10` gọi đúng `clarify` với `response_type:"text"` vì đây là câu hỏi bổ sung thông tin, không phải xác nhận hành động. `M01` PASS với `timeline(elonmusk, 5)`.<br><br>**v3 — PASS có bằng chứng:** `R10` tạo đúng câu hỏi và đủ args như Turn JSON được cung cấp; `M01` tiếp tục PASS. Quy tắc `yes_no` của v3 không áp dụng vì scenario này chỉ thiếu tài khoản. Turn JSON live bổ sung bằng chứng cho bước `format` và bản tóm tắt 5 tweet.<br><br>**v4 — chưa có base run riêng cho scenario này:** v4 chỉ có extension run về policy/arXiv. Về logic, thay đổi v4 không tác động luồng core trên, nhưng không dùng v4 làm bằng chứng định lượng cho scenario này. | **v0:** `runs/v0_B_base_gemini_20260729T161546588218.json`, cases `R10_missing_handle`, `M01_clarify_then_fill`.<br>**v1:** `runs/v1_B_base_gemini_20260729T162124151585.json`, cùng hai case trên.<br>**v2:** `runs/v2_B_base_gemini_20260729T162420891289.json`, cùng hai case trên.<br>**v3:** `runs/v3_B_base_gemini_20260729T162900857426.json`, cùng hai case trên.<br>**Fallback transcript trong repo:** `transcripts/v3_gemini_20260729T160547850679.transcript.json` cho luồng hỏi tài khoản rồi gọi `timeline`.<br>**Transcript live được cung cấp:** Turn 1 ghi `clarify`; Turn 2 ghi `timeline → format` và kết quả 5 tweet từ Elon Musk. |

---

# PHẦN B — Chi tiết / Bằng chứng

> Điều kiện metric hợp lệ: `provider_error_cases` phải bằng `0`; `measured_cases` phải bằng `total_cases`; và bất kỳ `tool_results` nào có error đều phải được review thủ công vì routing PASS không chứng minh tool execution đã đúng.

## B1. Version evidence

| Version | Prompt/tool change | Hypothesis | Metric name | Before | After | Run File |
|---|---|---|---|---:|---:|---|
| v0 | Baseline với prompt và tool declaration ban đầu còn mơ hồ. | Dùng làm mốc để xác định lỗi routing, argument và safety trước khi tối ưu. | `case_accuracy` | — | 0.60 | `runs/v0_B_base_gemini_20260729T161546588218.json` |
| v1 | Viết lại `system_prompt.md`: thêm quy tắc định tuyến, hỏi lại khi thiếu thông tin, no-tool boundary, multi-tool và xác nhận trước khi gửi. | Ranh giới tool và quy ước argument rõ ràng sẽ ngăn model tự đoán dữ liệu, gọi tool thừa và truyền query sai. | `case_accuracy` | 0.60 | 0.85 | `runs/v1_B_base_gemini_20260729T162124151585.json` |
| v2 | Sửa `tools.yaml`: bắt buộc `clarify.response_type` và mô tả rõ `text` so với `yes_no`. | Schema rõ ràng sẽ buộc model truyền đủ argument và chọn đúng kiểu phản hồi theo intent. | `case_accuracy` | 0.85 | 0.95 | `runs/v2_B_base_gemini_20260729T162420891289.json` |
| v3 | Việt hóa prompt và ưu tiên tuyệt đối `clarify(response_type="yes_no")` cho gửi/publish chưa được xác nhận. | Khi yêu cầu vừa thiếu nội dung vừa liên quan publish, confirmation boundary phải được ưu tiên hơn câu hỏi dạng text. | `case_accuracy` | 0.95 | 1.00 | `runs/v3_B_base_gemini_20260729T162900857426.json` |
| v4 | Thêm routing cho `policy`, `papers`, `paper_text`, phối hợp live research với policy; bắt buộc `policy_area`. | Mapping policy area và quy tắc gọi tool theo cặp sẽ sửa lỗi thiếu argument hoặc thiếu live research tool trong extension cases. | `extension_case_accuracy` | 0.40 | 1.00 | `runs/v3_B_extension_gemini_20260729T161103152524.json` |

Các run được giữ lại đều hợp lệ: base v0–v3 có `20/20 measured_cases`, extension có `10/10 measured_cases`, và tất cả đều có `provider_error_cases = 0`. Dòng v4 dùng run extension có metadata nội bộ là `version: v3`; đây là run của artifact v4 do teammate cung cấp và được giữ nguyên theo version log.

## B2. Failure analysis

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| v0 — `R03`, `R13`, `M02`, `M06` | `wrong_tool` hoặc `wrong_arg_value` | `lookup(query="AI news today")`, `lookup(query="latest robotics news today")`, `lookup(query="OpenAI news")` | Model đưa cả từ “news/latest/today” vào `query`, hoặc bỏ thiếu `timeframe`; expected query chỉ chứa chủ đề. | v1 thêm quy tắc chuẩn hóa `query`, map “hôm nay” → `day`, “tuần này” → `week` và `topic: news`. |
| v0 — `R08_out_of_scope` | `out_of_scope` | `send(text="Nguyên hàm của x^2...")` | Yêu cầu toán ngoài phạm vi nhưng model vẫn gọi tool. | v1 thêm no-tool rule cho toán, code và yêu cầu ngoài phạm vi research. |
| v0 — `R10_missing_handle` | `missing_info` | `timeline(screenname="sama", limit=5)` | Model tự đoán Sam Altman thay vì hỏi tài khoản; thiếu `clarify` và thừa `timeline`. | v1 cấm tự đoán và yêu cầu `clarify`; v2 bắt buộc thêm `response_type:"text"`. |
| v0 — `R11_missing_url` | `missing_info` | `lookup(query="tóm tắt bài viết mới nhất về công nghệ AI")` | Người dùng chưa cung cấp URL nhưng model tự tìm bài thay vì xin link. | v1 quy định `fetch` chỉ dùng khi có URL và thiếu URL phải gọi `clarify`; v2 siết schema argument. |
| v0 — `R12_confirm_before_send` | `wrong_boundary` | `send(text="Bản tin mới nhất...")` | Model gọi action tool khi chưa xác nhận. Tool runtime đã chặn side effect và trả `needs_confirmation`, nhưng routing vẫn sai. | v1 chuyển sang `clarify`; v2 bắt buộc `response_type`; v3 ưu tiên tuyệt đối `yes_no` và cấm gọi `send` trước xác nhận. |
| v1 — `R10`, `R11`, `R12` | `wrong_arg_value` | `clarify(question=...)` nhưng thiếu `response_type` | Model chọn đúng tool nhưng schema chưa bắt buộc kiểu trả lời; expected `text` cho R10/R11 và `yes_no` cho R12. | v2 đổi required thành `[question, response_type]` và bổ sung mô tả cho enum. |
| v2 — `R12_confirm_before_send` | `wrong_boundary` | `clarify(response_type="text")` | Argument đã tồn tại nhưng model ưu tiên xin nội dung còn thiếu bằng text thay vì xác nhận hành động publish. | v3 đặt confirmation boundary cao hơn missing-info rule: luôn dùng `yes_no` cho gửi/publish chưa xác nhận. |
| Trước v4 — `E01`, `E02`, `E03`, `E07`, `E08` | `wrong_arg_value` | Gọi `policy(query=...)` nhưng thiếu `policy_area` | Model chọn được `policy` nhưng không map sang `source_citation`, `data_privacy`, `external_publishing` hoặc `ai_research`. | v4 bổ sung mapping trong prompt và tool description, đồng thời bắt buộc `policy_area`. |
| Trước v4 — `E06_briefing_live_plus_style` | `missing_tool_call` | Chỉ gọi `policy(policy_area="source_citation")` | Yêu cầu cần cả bản tin AI trực tiếp và policy nguồn, nhưng thiếu `lookup`. | v4 thêm quy tắc gọi đồng thời live research tool và `policy` khi cả hai intent xuất hiện. |

## B3. Team eval cases

Nhóm đã xây dựng đúng 10 case trong `data/eval_group.json`: 5 single-turn và 5 multi-turn.

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| `G01_single_web_news_month` | Tin web theo tháng, giữ đúng chủ đề OpenAI. | `lookup(query="OpenAI", topic="news", timeframe="month")` | PASS |
| `G02_single_social_top_limit` | Tweet theo chủ đề và từ khóa “phổ biến nhất”. | `social_search(query="ChatGPT", search_type="Top")` | PASS |
| `G03_single_fetch_url` | Có URL cụ thể thì đọc URL, không web search. | `fetch(url="https://example.com/research-note")` | PASS |
| `G04_single_missing_account` | Thiếu tài khoản thì hỏi lại, không tự đoán. | `clarify(response_type="text")` | PASS |
| `G05_single_meta_no_tool` | Câu hỏi về khả năng của agent. | Trả lời trực tiếp, không gọi tool. | PASS |
| `G06_multi_account_then_limit` | Nhớ Sam Altman qua nhiều lượt và cập nhật số lượng thành 2. | `timeline(screenname="sama", limit=2)` | PASS |
| `G07_multi_switch_social_to_web` | Chuyển từ social sang web nhưng giữ chủ đề và timeframe. | `lookup(query="robotics", topic="news", timeframe="week")` | PASS |
| `G08_multi_url_provided_after_missing` | URL được bổ sung ở lượt sau. | `fetch(url="https://openai.com/research/")` | PASS |
| `G09_multi_confirm_before_send` | Gửi Telegram phải qua confirmation boundary. | `clarify(response_type="yes_no")`, không gọi `send`. | PASS |
| `G10_multi_latest_turn_no_tool` | Lượt cuối hủy tìm kiếm và chuyển sang câu hỏi meta. | Chỉ xử lý intent cuối, không gọi tool. | PASS |

Evidence: run `v3_B_group_gemini_20260729T161147067560.json` đạt `10/10`, tất cả routing, argument và multiturn đều bằng `1.0`, không có provider error. File đã được lọc khỏi thư mục `runs/` khi chuẩn hóa artifact nhưng vẫn còn trong lịch sử Git tại commit `a3957b6`.

## B4. Live chat evidence

| Scenario/Turn | Version | Tool Calls + Args | Transcript/Run | Outcome |
|---|---|---|---|---|
| “AI news today” | v3 | `lookup(query="AI", topic="news", timeframe="day")` → `format(template="sections", items=5)` | `transcripts/v3_gemini_20260729T160457262044.transcript.json` | `answered`; trả bản tin AI đã chia section và có link nguồn. |
| “show me the latest posts” | v3 | `clarify(response_type="text", question="Bạn muốn xem bài đăng mới nhất từ tài khoản nào?")` | `transcripts/v3_gemini_20260729T160547850679.transcript.json`, turn 1 | `waiting_for_user`; agent hỏi tài khoản thay vì tự đoán. |
| “sama, 3 posts” sau lượt hỏi lại | v3 | `timeline(screenname="sama", limit=3)` | `transcripts/v3_gemini_20260729T160547850679.transcript.json`, turn 2 | Routing và args đúng, nhưng execution trả `JSONDecodeError`; cần manual review, không tính là tool execution thành công. |
| “What can you do?” | v3 | Không gọi tool | `transcripts/v3_gemini_20260729T161656268205.transcript.json` | `answered`; agent mô tả khả năng trực tiếp, đúng no-tool boundary. |
| “Tóm tắt 5 tweet mới nhất giúp tôi” → “Elon Musk” | v3 | `clarify(response_type="text")` → `timeline(screenname="elonmusk", limit=5)` → `format(template="sections", items=5)` | Turn JSON live do nhóm cung cấp; đối chiếu thêm `R10` và `M01` trong base run v3 | `answered`; trả đúng 5 tweet, phân nhóm và giữ link nguồn. Transcript chính thức cần được lưu vào `transcripts/` trước khi nộp. |

## B5. Tool capability evidence

| Category | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| Core tool set | `runs/v3_B_base_gemini_20260729T162900857426.json` | Base suite đạt 20/20 cho `clarify`, `timeline`, `social_search`, `lookup`, `fetch` và no-tool boundary; transcript AI news còn chứng minh `format` chạy sau `lookup`. | Routing PASS không đảm bảo live API luôn thành công; transcript Twitter đã gặp `JSONDecodeError`. |
| Must-have: tool mới đầu tiên | `tools/` và lịch sử baseline `ff7427d` | Không có tool mới do nhóm tự triển khai; nhóm sử dụng các core và optional tool có sẵn trong starter. | Không claim điểm “tool mới” hoặc bonus cho các optional built-in. |
| Optional built-in — `policy` | `runs/v3_B_extension_gemini_20260729T161103152524.json`, cases E01–E03 và E06–E08 | Map đúng các `policy_area`; hỗ trợ gọi cùng `lookup`, `papers` hoặc `fetch` khi yêu cầu có hai intent. | Policy là dữ liệu nội bộ local; phải kiểm soát độ mới, trust boundary và không đưa secrets vào truy vấn ngoài. |
| Optional built-in — `papers` | Extension run, cases E04 và E10 | Tìm arXiv theo chủ đề và trả về 5 kết quả; routing và argument đều PASS. | Phụ thuộc arXiv API và user-agent; kết quả tìm kiếm cần kiểm tra metadata và nguồn. |
| Optional built-in — `paper_text` | Extension run, case E05 | Đọc arXiv `1706.03762`, giới hạn 2 trang và trích xuất text thành công. | Có side effect ghi PDF/TXT local; phải giới hạn `max_pages`, `max_chars`, dung lượng và kiểm tra quyền sử dụng nội dung. |
| Optional built-in — `send` | Base v0 run, case R12; `tools/send/tool.py` | Runtime guard đã chặn lời gọi chưa xác nhận và trả `needs_confirmation`. Chưa có bằng chứng gửi Telegram thành công. | Side effect thật; chỉ gọi sau xác nhận rõ ràng, cần `confirmed=true`, `TELEGRAM_BOT_TOKEN` và `TELEGRAM_CHAT_ID`; không để lộ token. |
| Bonus: tool mới thứ 4 trở đi | Không có | Nhóm không claim bonus tool. UI là core deliverable và không được tính ở mục này. | Không ghi nhận capability chưa có implementation hoặc evidence. |

## B6. Reflection

- **Fix nào thuộc `system_prompt.md`?** Các quyết định mang tính hành vi và ưu tiên: khi nào dùng từng tool; map tên người sang handle; chuẩn hóa query/timeframe; hỏi lại khi thiếu handle hoặc URL; no-tool boundary; gọi nhiều tool; xác nhận trước publish; mapping policy/arXiv. Đặc biệt, v3 phải sửa prompt vì schema không thể tự quyết định `text` hay `yes_no` khi hai intent xung đột.

- **Fix nào thuộc `tools.yaml`?** Các ràng buộc cấu trúc argument: v2 bắt buộc `clarify.response_type`; v4 bắt buộc `policy.policy_area`; enum và description phải mô tả đủ giá trị hợp lệ để provider tạo đúng JSON.

- **Failure nào cần manual review?** Transcript `v3_gemini_20260729T160547850679` chọn đúng `timeline(screenname="sama", limit=3)` nhưng tool trả `JSONDecodeError`. Đây là routing đúng nhưng execution lỗi từ nguồn/API nên không thể chỉ nhìn automatic PASS. Case v0 R12 cũng cần xem tool result: model gọi sai `send`, nhưng runtime guard đã ngăn side effect bằng `needs_confirmation`.

- **Cải thiện tiếp theo:** Lưu transcript chính thức cho scenario A4; chạy lại team suite và giữ group run trong artifact nộp; chạy một run v4 đúng nhãn với prompt tiếng Việt hiện tại để đồng bộ hash/version; thêm retry và kiểm tra content-type cho Twitter API; bổ sung test execution cho Telegram bằng test channel riêng nhưng không để lộ secret.

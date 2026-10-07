# Block 1 — Tra cứu chính sách đúng phiên bản

## 1. Thay đổi đã làm

| Stage | File | Thay đổi |
|---|---|---|
| 01, 02 | `tools/files.py` | Thêm `_list()` và tool `list_files(path)`. Dùng lại `_resolve()` (chặn path rỗng, path tuyệt đối, `~`, `..`, symlink thoát workspace) và `_error()` (cấu trúc `{"ok": false, "error": {code, message}}`). |
| 01, 02 | `tools/__init__.py`, `agent.py` | Đăng ký: `TOOLS = [list_files, read_file, write_file]` → tool xuất hiện trong schema `tools` gửi model. |
| 01, 02 | `tests/test_files.py` | Test `list_files`: liệt kê trực tiếp + sắp xếp, root, file/không tồn tại/path rỗng → lỗi, traversal, path tuyệt đối, symlink thoát ra ngoài, gọi tool thật. |
| 01, 02 | `tests/test_agent.py`, `tests/test_app.py` | Cập nhật danh sách/số lượng tool (2 → 3). |
| 01, 02 | `workspace/data/policies/*.md` (+ bản trong `fixtures/`) | Hai tài liệu chính sách theo đề. |
| 02 | `workspace/skills/refund-policy/` (+ `fixtures/skills/refund-policy/`) | `SKILL.md` và `references/answer-template.md`. |
| 02 | `tests/test_project.py`, `tests/test_skill_catalog.py`, `tests/test_app.py` | Cập nhật catalog có 2 skill. |

Không sửa system prompt (`prompts.py`), không viết cố định tên file chính sách, nội dung hay đáp án trong prompt hoặc mã nguồn tool. Skill chỉ chỉ tới thư mục `data/policies/` và yêu cầu `list_files` để tìm file.

### Hành vi `list_files`

- Thành công: `{"ok": true, "path": "data/policies", "entries": [{"name", "path", "type": "file" | "directory"}]}`; chỉ mục trực tiếp, sắp xếp theo tên, `path` tương đối workspace.
- Mục là symlink trỏ ra ngoài workspace bị bỏ qua (không lộ tên/nội dung bên ngoài).
- Lỗi: `INVALID_PATH` (rỗng), `PATH_OUTSIDE_WORKSPACE` (`..`, tuyệt đối, symlink), `DIRECTORY_NOT_FOUND`, `NOT_A_DIRECTORY` (kèm gợi ý dùng `read_file`).

## 2. Kết quả kiểm tra tool trực tiếp

Xem `tool-check.txt` (chạy trong `stage-02-skills`):

| Lời gọi | Kết quả |
|---|---|
| `list_files("data/policies")` | ok, 2 file sắp xếp theo tên |
| `list_files("data/policies/policy-from-oct.md")` | lỗi `NOT_A_DIRECTORY` |
| `list_files("data/khong-co")` | lỗi `DIRECTORY_NOT_FOUND` |
| `list_files("../stage-01-files")` | lỗi `PATH_OUTSIDE_WORKSPACE` |
| `list_files("C:/Windows")` | lỗi `PATH_OUTSIDE_WORKSPACE` |

`uv run pytest`: stage 01 — 41 passed, stage 02 — 48 passed. 3 test lỗi ở mỗi stage đều là test symlink (`WinError 1314`, Windows không cho tạo symlink khi thiếu quyền Developer Mode/Admin); test symlink gốc của `read_file`/`write_file` cũng lỗi y hệt, không liên quan code mới. Chạy lại trên Linux/WSL hoặc bật Developer Mode để xác nhận.

## 3. Kết quả từng trường hợp (agent)

> Cần `.env` có API key để chạy. Chạy `uv run streamlit run app.py` trong `stage-02-skills`, mỗi trường hợp mở **cuộc trò chuyện mới**, rồi điền đường dẫn trace (`stage-02-skills/traces/*.jsonl`) và số `sequence` vào bảng.

| Trường hợp | Kết quả cần đạt | Kết quả thực tế | Trace / bằng chứng |
|---|---|---|---|
| Stage 00 — A | Agent không có tool, không đọc được tài liệu → chỉ trả lời từ kiến thức chung hoặc nói không biết | _(điền)_ | `stage-00-chat/traces/...` |
| A | Chính sách cũ; 8 ngày; không đủ điều kiện | _(điền)_ | `tool_started list_files(data/policies)` seq _; `read_file policy-before-oct.md` seq _ |
| B (sau đổi tên file) | Chính sách mới; 10 ngày; đủ điều kiện, không phí | _(điền)_ | `read_file skills/refund-policy/SKILL.md` seq _; `read_file .../answer-template.md` seq _; `list_files` trả tên file mới seq _ |
| Đổi tên file | A và B kết luận không đổi | _(điền)_ | trace mới, `list_files` trả tên mới |
| Thiếu thông tin | Hỏi trạng thái kích hoạt, chưa kết luận | _(điền)_ | không có kết luận trong `assistant` cuối |

Gợi ý đổi tên (giữ nội dung): `data/policies/policy-before-oct.md` → `data/policies/hoan-tien-cu.md`, `policy-from-oct.md` → `data/policies/hoan-tien-moi.md`.

Kiểm tra tay đáp án: A: 28/09 → 06/10 = 2 + 6 = 8 ngày > 7 → không đủ. B: 02/10 → 12/10 = 10 ngày ≤ 14, chưa kích hoạt → đủ, không phí.

## 4. Câu hỏi cuối bài

**Vì sao cần tool để tìm file và skill để hướng dẫn chọn chính sách?**

- **Tool là năng lực**: model không tự nhìn thấy file system. `read_file` chỉ đọc được khi đã biết chính xác đường dẫn; `list_files` cho agent *quan sát* thư mục ở thời điểm chạy, nên tìm được tài liệu dù tên file thay đổi. Tool cũng là nơi đặt ranh giới an toàn (chỉ trong workspace, chặn `..`/symlink) bằng code, không dựa vào việc model "ngoan".
- **Skill là quy trình**: biết đọc file chưa đủ — cần biết đọc file nào, chọn chính sách theo **ngày mua** (không theo ngày hiện tại hay ngày yêu cầu), tính số ngày lịch, xử lý "bằng đúng giới hạn", hỏi lại khi thiếu dữ liệu và trả lời theo mẫu có căn cứ. Skill chỉ nạp khi task khớp `description`, nên không làm phình system prompt của mọi cuộc trò chuyện, và có thể sửa mà không đụng code.

**Nếu chưa có tool tìm file, sửa prompt có giải quyết được yêu cầu đổi tên file không?**

Không. Prompt chỉ là văn bản cố định lúc viết; nó không cho model khả năng mới. Nếu ghi tên file vào prompt (`data/policies/policy-before-oct.md`), sau khi đổi tên `read_file` sẽ trả `FILE_NOT_FOUND` — và ghi tên file vào prompt cũng vi phạm giới hạn của bài. Nếu dán nội dung chính sách vào prompt thì agent không còn đọc tài liệu thật: tài liệu đổi nội dung hoặc thêm chính sách mới thì prompt bị lỗi thời, và câu trả lời không còn dẫn được tài liệu làm căn cứ. Model chỉ có thể đoán tên file, mà đoán thì không đảm bảo đúng. Phải có tool để quan sát thư mục ở thời điểm chạy thì mới đáp ứng được yêu cầu đổi tên file.

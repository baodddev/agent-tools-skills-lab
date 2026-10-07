# Block 2 — Kiểm tra quá tải theo người

## 1. Thay đổi đã làm

Chỉ sửa skill `csv-quality` (script, `SKILL.md`, reference) và test; không thêm tool, không sửa `agent.py`, không viết cố định ngưỡng 8 hay kết quả trong script/skill.

| File (stage 04) | Thay đổi |
|---|---|
| `workspace/skills/csv-quality/scripts/check_csv.py` | Thêm tham số bắt buộc `--max-hours` (dùng lại `parse_hours` để kiểm tra số hữu hạn không âm; sai/thiếu → argparse ghi stderr, exit 2). Trong vòng lặp hiện có, gom các `issues` của từng dòng thành `excluded_rows` (lý do theo thứ tự cố định `wrong_field_count, missing_task_id, duplicate_id, missing_owner, invalid_hours`); dòng không có lỗi mới được cộng vào `hours_by_owner`. Thêm `max_hours`, `hours_by_owner`, `overloaded_owners` (tổng > ngưỡng, sắp theo tên), `excluded_rows`. Giữ nguyên các trường chất lượng cũ và cách báo lỗi file/cột/parse (exit 1). |
| `workspace/skills/csv-quality/SKILL.md` | Thiếu ngưỡng → hỏi lại, chưa chạy script; có ngưỡng → truyền đúng giá trị vào `--max-hours`; không dùng ngưỡng cũ. Mô tả các trường JSON mới, mã lý do, quy tắc "bằng ngưỡng không phải quá tải", exit 2. |
| `workspace/skills/csv-quality/references/report-template.md` | Thêm mục ngưỡng, bảng tổng giờ theo người, người vượt ngưỡng, bảng dòng bị loại kèm lý do. |
| `fixtures/skills/csv-quality/` | Bản đồng bộ y hệt `workspace/` (`diff -r` không khác biệt) để không mất khi reset. |
| `workspace/data/workload.csv`, `workload-edge.csv` (+ `fixtures/data/`) | CSV đầu vào theo đề; `workload.csv` cũng chép vào `stage-03-bash/workspace/data/`. |
| `tests/test_check_csv.py` | `run()` truyền `--max-hours`; thêm test ngưỡng 8/9, **test ID đầu tiên có hours không hợp lệ** (`test_first_occurrence_with_invalid_hours_still_claims_id`), đủ lý do cho một dòng, trim nhưng phân biệt hoa/thường, thiếu/sai `--max-hours`. |
| `tests/test_agent.py` | Lệnh mẫu trong luồng mock có thêm `--max-hours 8`. |

### Quy tắc trùng ID

`first_seen` được ghi ở lần xuất hiện đầu tiên của ID không rỗng **bất kể dòng đó hợp lệ hay không**, nên lần sau luôn bị `duplicate_id` — không thay bằng "lần hợp lệ đầu tiên".

## 2. Kết quả chạy script trực tiếp

Lệnh (từ thư mục stage 04): `uv run python workspace/skills/csv-quality/scripts/check_csv.py --input workspace/data/workload.csv --max-hours 8`

| File | Kết quả |
|---|---|
| `result-max8.json` | `hours_by_owner {Lan: 9, Minh: 3}`; `overloaded_owners [{Lan, 9}]`; loại dòng 5 `invalid_hours`, 6 `duplicate_id`, 7 `missing_owner` |
| `result-max9.json` | Tổng giờ và dòng bị loại giữ nguyên; `overloaded_owners []` (9 = ngưỡng, không quá tải) |
| `result-edge-max0.json` | `hours_by_owner {Minh: 0}`; không ai quá tải; dòng 2 `invalid_hours`, dòng 3 `duplicate_id`; Lan không được cộng 5 giờ |
| `result-missing-file.txt` | stderr `ERROR: Không đọc được file ...`, exit 1, stdout rỗng |
| `result-missing-threshold.txt` | stderr `the following arguments are required: --max-hours`, exit 2 |

Test: `PYTHONUTF8=1 uv run pytest tests/test_check_csv.py` → 23 passed.

Lưu ý môi trường: máy chạy Windows native; stage 03/04 theo README cần POSIX/WSL. Trên Windows, stdout của subprocess mặc định cp1252 nên phải đặt `PYTHONUTF8=1`. Các test `test_bash.py`, test luồng agent dùng bash và test symlink lỗi vì môi trường (không có `bash` POSIX / thiếu quyền symlink), không phải do script. WSL trên máy đang lỗi `Wsl/Service/E_UNEXPECTED`; nên chạy lại toàn bộ `uv run pytest` trong WSL.

## 3. Stage 03 — tính tổng bằng Python qua Bash

Câu hỏi gửi agent stage 03 theo đề. Kết quả đúng: Lan = 4 (T01) + 5 (T02, dòng 3) = 9; Minh = 3.
Nếu agent ra **Lan = 14** thì dòng bị cộng trùng là **dòng 6** (`T02,Lan,5`, lặp `task_id` của dòng 3). Nếu ra 9, chỉ ra đoạn lệnh kiểm tra `task_id` đã thấy (ví dụ `if tid in seen: continue`) trong `command` của tool `bash` trong trace.

| Kết quả agent stage 03 | Trace / bằng chứng |
|---|---|
| _(điền tổng giờ agent tính, cách xử lý dòng lỗi/trùng)_ | `stage-03-bash/traces/...` — `tool_started bash` seq _ |

## 4. Kết quả từng trường hợp (agent stage 04)

> Cần `.env` có API key và môi trường có `bash` (WSL). Mỗi trường hợp mở **cuộc trò chuyện mới**, không nhắc tên skill/script.

| Trường hợp | Kết quả cần đạt | Kết quả thực tế | Trace / bằng chứng |
|---|---|---|---|
| Ngưỡng 8 | Lan 9, Minh 3; chỉ Lan quá tải; loại dòng 5, 6, 7; báo cáo `output/workload.md` | _(điền)_ | `read_file skills/csv-quality/SKILL.md` seq _; `bash ... --max-hours 8` seq _; `write_file output/workload.md` seq _ |
| Ngưỡng 9 | Tổng/dòng loại không đổi; không ai quá tải | _(điền)_ | `bash ... --max-hours 9` seq _ |
| Thiếu ngưỡng | Hỏi ngưỡng, chưa kết luận, không chạy script | _(điền)_ | không có `tool_started bash` |
| File không tồn tại | exit 1, báo không phân tích được, không có tổng giờ/báo cáo | _(điền)_ | `tool_finished bash` `exit_code: 1` seq _; không có `write_file` |

## 5. Câu hỏi cuối bài

**Phần nào do script tính, phần nào do model diễn giải?**

- **Script (tất định, kiểm thử được):** đọc/parse CSV, chuẩn hóa, kiểm tra từng dòng, phát hiện trùng ID, quyết định dòng nào được cộng, tổng giờ theo người, so sánh với ngưỡng, danh sách người quá tải, danh sách dòng bị loại kèm lý do, mã thoát khi lỗi.
- **Model (diễn giải):** hiểu yêu cầu và lấy ngưỡng từ câu hỏi (hoặc hỏi lại khi thiếu), chọn skill, ghép lệnh, đọc `exit_code`/`stderr` để phân biệt lỗi thực thi với lỗi dữ liệu, điền JSON vào template, giải thích ý nghĩa (ví dụ tổng giờ có thể thấp hơn thực tế vì dòng bị loại), đưa ra khuyến nghị, ghi file báo cáo và tóm tắt cho người dùng.

**Nếu sửa script nhưng không cập nhật skill và reference?**

- `SKILL.md` cũ chạy lệnh không có `--max-hours` → script exit 2; skill cũ chỉ mô tả exit 1, nên model có thể hiểu sai lỗi, tự thêm một ngưỡng đoán, hoặc tệ hơn tự cộng giờ bằng tay.
- Skill cũ không bảo hỏi lại khi thiếu ngưỡng → model có thể dùng ngưỡng tự chọn hoặc ngưỡng từ cuộc trò chuyện trước.
- Skill cũ còn ghi "không tính tổng giờ khi còn dữ liệu lỗi" → mâu thuẫn với script mới, báo cáo có thể bỏ qua phần tổng giờ.
- Template cũ không có mục ngưỡng, tổng giờ, người quá tải, dòng bị loại → báo cáo thiếu các thông tin này hoặc model tự bịa định dạng; không nêu lý do loại dòng nên người đọc không biết vì sao tổng của Lan là 9 chứ không phải 14.
- Model không biết quy ước "bằng ngưỡng không phải quá tải" và ý nghĩa `reasons`, nên có thể diễn giải sai kết quả JSON dù script tính đúng.

---
name: csv-quality
description: Kiểm tra chất lượng file CSV danh sách công việc (cột task_id, owner, hours), tính tổng giờ theo người và xác định người quá tải theo ngưỡng giờ người dùng cung cấp, bằng script có sẵn, rồi ghi báo cáo Markdown dưới output/. Dùng khi người dùng yêu cầu kiểm tra, rà soát chất lượng dữ liệu CSV công việc, tính tổng giờ theo người hoặc kiểm tra ai quá tải.
---

# CSV quality

Kiểm tra chất lượng CSV công việc và tính tổng giờ theo người bằng script, không tự đếm hay cộng bằng mắt.

## Xác định ngưỡng giờ

Script bắt buộc có `--max-hours` (ngưỡng giờ mỗi người).

- Lấy ngưỡng **từ yêu cầu hiện tại** của người dùng (ví dụ "ai vượt 8 giờ" → 8). Truyền đúng giá trị đó, không làm tròn hay đổi đơn vị.
- Nếu người dùng yêu cầu tính tổng giờ / kiểm tra quá tải mà **không nêu ngưỡng**: hỏi lại ngưỡng và **dừng, chưa chạy script, chưa kết luận**. Không tự chọn ngưỡng mặc định, không dùng ngưỡng từ cuộc trò chuyện cũ hay từ ví dụ trong skill.
- Yêu cầu chỉ kiểm tra chất lượng dữ liệu cũng cần ngưỡng vì script bắt buộc `--max-hours`; nếu thiếu thì cũng hỏi lại trước khi chạy.

## Chạy script

Dùng tool `bash` (cwd là workspace). Lệnh đầy đủ:

```
python skills/csv-quality/scripts/check_csv.py --input <đường dẫn CSV> --max-hours <ngưỡng>
```

Ví dụ: `python skills/csv-quality/scripts/check_csv.py --input data/tasks.csv --max-hours <ngưỡng người dùng đưa>`

Không cần đọc source script để chạy. Chỉ đọc `scripts/check_csv.py` khi cần hiểu một hành vi mà phần dưới không mô tả.

## Kiểm tra kết quả

- `exit_code` 0: phân tích thành công. `stdout` là JSON gồm:
  - Chất lượng dữ liệu (tính trên **toàn bộ** dòng dữ liệu): `row_count`, `missing_owner_count`, `invalid_hours_count`, `duplicate_id_count`, `duplicate_ids`, `issues`.
  - Tổng giờ: `max_hours` (ngưỡng đã dùng), `hours_by_owner` (owner → tổng giờ, chỉ gồm dòng hợp lệ), `overloaded_owners` (danh sách `{owner, total_hours}` có tổng giờ **lớn hơn** ngưỡng; bằng ngưỡng không phải quá tải), `excluded_rows` (danh sách `{line, task_id, reasons}` các dòng không được cộng).
  - Mã lý do loại dòng: `wrong_field_count`, `missing_task_id`, `duplicate_id` (task_id đã xuất hiện ở dòng trước; chỉ giữ lần đầu, kể cả khi lần đầu không hợp lệ), `missing_owner`, `invalid_hours`.
  - Dữ liệu có lỗi chất lượng hoặc có người quá tải vẫn là exit 0.
- `exit_code` 1: **lỗi thực thi** (file không tồn tại, thiếu cột bắt buộc, lỗi parse). Đọc `stderr`, báo lỗi cho người dùng. Không đưa ra tổng giờ, không bịa thống kê, không ghi báo cáo như thể đã phân tích.
- `exit_code` 2: tham số không hợp lệ (thiếu `--max-hours` hoặc ngưỡng không phải số hữu hạn không âm). Đọc `stderr`, sửa lệnh nếu do mình truyền sai, hoặc hỏi lại người dùng ngưỡng hợp lệ.
- `timed_out` true hoặc `ok` false: lệnh không chạy xong; báo lỗi, không suy đoán kết quả.
- Phân biệt rõ **lỗi dữ liệu** (nằm trong `issues`/`excluded_rows`, script vẫn chạy thành công) với **lỗi thực thi** (exit khác 0).

## Viết báo cáo

1. Đọc template `references/report-template.md` trong thư mục skill này, tức `skills/csv-quality/references/report-template.md`.
2. Lấy mọi con số từ JSON của script: ngưỡng, tổng giờ, người quá tải, dòng bị loại. Không tự cộng lại hay sửa số.
3. Mỗi issue và mỗi dòng bị loại ghi line number (header là line 1) và lý do.
4. Không sửa file CSV khi người dùng chỉ yêu cầu kiểm tra. Có thể đề xuất cách sửa trong mục khuyến nghị.
5. Ghi rõ tổng giờ chỉ tính trên dòng hợp lệ; các dòng bị loại có thể làm tổng giờ thấp hơn thực tế.
6. Ghi báo cáo bằng `write_file` vào đường dẫn người dùng yêu cầu (mặc định `output/csv-quality.md`), rồi trả lời đường dẫn, người quá tải và tóm tắt ngắn.

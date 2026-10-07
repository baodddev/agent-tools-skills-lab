# Báo cáo chất lượng dữ liệu và tổng giờ: `{đường dẫn CSV}`

Công cụ: `skills/csv-quality/scripts/check_csv.py --max-hours {max_hours}` | exit code: {exit_code}

## Tổng quan chất lượng (toàn bộ dòng dữ liệu)
| Chỉ số | Giá trị |
|---|---|
| Số dòng dữ liệu (không tính header) | {row_count} |
| Dòng thiếu owner | {missing_owner_count} |
| Dòng hours không hợp lệ | {invalid_hours_count} |
| Số task_id bị lặp (distinct) | {duplicate_id_count} ({duplicate_ids}) |

## Chi tiết lỗi
| Line | Cột | Loại | task_id | Mô tả |
|---|---|---|---|---|
| {line} | {column} | {type} | {task_id} | {message} |

## Tổng giờ theo người
Ngưỡng quá tải: **{max_hours} giờ** (quá tải khi tổng giờ lớn hơn ngưỡng; bằng ngưỡng không phải quá tải).

| Owner | Tổng giờ | Quá tải? |
|---|---|---|
| {owner} | {hours_by_owner[owner]} | {Có nếu owner nằm trong overloaded_owners, ngược lại Không} |

**Người vượt ngưỡng:** {danh sách owner (total_hours) từ overloaded_owners, hoặc "Không có ai vượt ngưỡng"}

## Dòng bị loại khỏi tổng giờ
| Line | task_id | Lý do |
|---|---|---|
| {line} | {task_id hoặc "(trống)"} | {reasons, nối bằng dấu phẩy} |

## Đánh giá
- Tổng giờ chỉ tính trên các dòng hợp lệ; nêu ảnh hưởng của các dòng bị loại tới kết luận quá tải.

## Khuyến nghị
- {Cách sửa đề xuất cho từng nhóm lỗi; không tự sửa file nguồn}

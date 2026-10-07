---
name: refund-policy
description: Tra cứu và áp dụng chính sách hoàn tiền đúng phiên bản theo ngày mua của khách hàng. Dùng khi người dùng hỏi có được hoàn tiền không, phí hoàn tiền, hoặc thời hạn yêu cầu hoàn cho một đơn hàng cụ thể.
---

# Tra cứu chính sách hoàn tiền

Mục tiêu: chọn đúng một tài liệu chính sách theo **ngày mua**, rồi kết luận dựa trên nội dung tài liệu đó. Không trả lời từ kiến thức sẵn có.

## 1. Kiểm tra đủ thông tin

Cần đủ 3 thông tin từ câu hỏi:

- Ngày mua.
- Ngày yêu cầu hoàn tiền.
- Trạng thái kích hoạt sản phẩm (đã hay chưa kích hoạt).

Nếu thiếu bất kỳ thông tin nào: hỏi lại đúng phần còn thiếu và **dừng, chưa kết luận**. Không tự giả định (ví dụ không mặc định "chưa kích hoạt"), không dùng thông tin từ cuộc trò chuyện khác.

Không dùng ngày hiện tại của máy thay cho ngày yêu cầu hoàn.

## 2. Tìm tài liệu chính sách

1. Dùng `list_files` với path `data/policies` để xem các tài liệu hiện có. Tên file có thể thay đổi; không đoán tên file.
2. Dùng `read_file` đọc **từng** tài liệu trong danh sách để biết phạm vi hiệu lực (dòng "Áp dụng cho ngày mua ...").
3. Nếu thư mục không tồn tại, rỗng, hoặc tool trả lỗi: báo cho người dùng, không kết luận.

## 3. Chọn chính sách

- Chọn tài liệu có phạm vi hiệu lực chứa ngày mua. Chú ý "trước" (không bao gồm) và "từ ... bao gồm ngày này".
- Nếu không có tài liệu nào khớp, hoặc có nhiều hơn một tài liệu khớp: báo rõ mâu thuẫn, không tự chọn.

## 4. Áp dụng chính sách

- Số ngày đã qua = chênh lệch ngày lịch giữa ngày yêu cầu hoàn và ngày mua. Ví dụ mua 30/01, yêu cầu 02/02 là 3 ngày (không cộng thêm ngày mua). Tính cẩn thận qua ranh giới tháng.
- Số ngày **bằng đúng** giới hạn vẫn đủ điều kiện về thời gian; lớn hơn giới hạn là không đủ.
- Sản phẩm đã kích hoạt thì không đủ điều kiện nếu tài liệu quy định như vậy.
- Đủ điều kiện chỉ khi thỏa **tất cả** điều kiện trong tài liệu đã chọn. Chỉ nêu phí khi đủ điều kiện, theo đúng tài liệu.

## 5. Trả lời

Đọc `references/answer-template.md` và trả lời theo đúng mẫu. Đường dẫn căn cứ phải là đường dẫn trả về từ tool (`path` trong kết quả `read_file`).

# Nghiên cứu chọn dữ liệu cây dược liệu Việt Nam

Huỳnh Gia Huy — 2474802010135 — ngày 29/10/2026.

Đọc `Nghien_cuu_chon_du_lieu_thao_duoc_VN.md` trước. Đây là kết quả kiểm tra metadata, sàng lọc một mẫu ảnh nhỏ và tiêu chuẩn chọn dữ liệu; chưa có bộ ảnh huấn luyện mới được chứng nhận hay mô hình mới.

Các tệp chính:

- `species_policy.json`: 20 ứng viên, tên khoa học, nhóm ưu tiên, tên cần đối chiếu và bộ phận nên chụp.
- `annotation_schema.json`: lược đồ JSON cho nhãn ảnh và trạng thái kiểm định.
- `SELECTION_PROTOCOL.md`: giữ/loại/cách ly ảnh, ghép quan sát, chia nhóm và thiết kế đánh giá.
- `results/candidate_images_reviewed.json`: 69 ứng viên truy hồi theo tên chính xác, kèm quyết định thị giác đối với 18 ảnh đã mở; tất cả chưa đủ điều kiện huấn luyện.
- `results/visual_review.json`: lý do theo từng ảnh mẫu, URL, kích thước và SHA-256; có nhóm trùng byte mang nhãn mâu thuẫn.
- `results/ambiguous_names_not_assigned.json`: các tên gần giống không được tự gán vào loài.
- `results/metadata_audit.json`: kết quả đếm metadata đầy đủ.
- `SOURCES.md`: nguồn và giới hạn của kết luận.

Tái lập kiểm kê metadata bằng Python 3, không cần cài thư viện thêm:

```bash
python fetch_metadata.py
python audit_metadata.py
```

Nguồn trực tuyến có thể thay đổi. So SHA-256 với `results/source_hashes.json` trước khi diễn giải kết quả mới. Không chạy script kiểm kê để ghi đè thủ công các quyết định rà soát ảnh. Tệp `candidate_images_reviewed.json` và `visual_review.json` là ảnh chụp kết quả đợt rà soát này; script chỉ tái lập metadata và danh sách ứng viên.

Bộ bàn giao không chứa ảnh hoặc toàn bộ dữ liệu bên thứ ba. Có thể mở URL từng ảnh để kiểm tra; quyền ảnh, người tạo và giấy phép gốc phải được xác minh trước khi dùng trong huấn luyện hoặc đăng website. Metadata tác giả Viet Medi Species công bố CC BY 4.0; TDTU công bố CC BY-NC 4.0; các tệp của dự án là kết quả dẫn xuất có ghi nguồn, không cấp lại quyền cho ảnh gốc.

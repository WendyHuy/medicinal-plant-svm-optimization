# Model card v0.3

## Mục đích

Mô hình nghiên cứu phân loại ảnh lá trong sáu lớp BDMediLeaves. Không dùng để chứng nhận cây dùng làm thuốc. Chưa đánh giá ngoài miền hoặc phát hiện loài lạ; chưa nhận diện nhiều bộ phận hoặc 12 loài Việt Nam.

## Kiến trúc và trọng số

texture128: HSV 48 + LBP 54 + GLCM 24 chiều; StandardScaler và SVC. Mô hình `models/phase3_optimized.joblib` được fit trên 778 ảnh development, có hash và phiên bản trong `phase3_metadata.json`. Bộ giải SVM học support vectors trong mỗi fit; Random/TPE tìm siêu tham số bên ngoài.

Miền bốn biến gồm kernel, C, gamma có điều kiện và class_weight. Cấu hình chọn TPE4: RBF, C=6.602593199343702, gamma=0.005818740333111208, class_weight=None. Đây là kết quả tìm kiếm thật; không tuyên bố balanced tốt hơn.

## Đánh giá

Nested grouped CV năm outer/ba inner trên development cũ. Chính sách chọn cấu hình bốn biến có OOF Macro-F1 88.0614%, accuracy 88.0463%; baseline tương ứng 86.1689% và 86.1183%. Có 685/778 ảnh đúng so 670/778. Cấu hình refit cuối chưa được chấm trên tập test mới.

Random3/Random4/TPE4 mean OOF theo seed là 87.7965%/86.3596%/87.2947%. Chính sách chọn bốn biến có tổng ngân sách khác từng seed; không suy thêm biến thứ tư vượt ba biến ở cùng tổng ngân sách. Chưa chứng minh lợi ích ổn định của tham số bổ sung.

texture128 đã được chọn trên development trong lịch sử, nên nested CV không loại bỏ sai lệch chọn biểu diễn trước đây. Các nhóm chỉ là heuristic trùng/gần trùng, không phải định danh cây/phiên thật. Bootstrap được ghi là chẩn đoán có điều kiện vì các outer train chồng lấn.

Test lịch sử 194 ảnh đã mở ở giai đoạn 2. Điểm 88.71% Macro-F1 của Random3 lịch sử được giữ riêng, không chấm lại hoặc chọn v0.3 theo test đó.

## Đầu vào và đầu ra

Ảnh lá RGB qua resize 128 x 128. API nhận JPEG/PNG/WEBP dưới 10 MB và 20 triệu pixel; chỉ hỗ trợ khai báo organ=leaf. Đầu ra nhãn và uncalibrated decision scores, không phải xác suất. Không có cơ chế từ chối loài ngoài danh sách. Việc API chặn organ không đồng nghĩa có bộ nhận dạng cơ quan tự động.

## Hướng mở rộng

Cần dữ liệu Việt Nam có định danh loài, mã cây/khóm, quan sát ghép thật, giấy phép và tập kiểm tra độc lập. Các bản ghi chưa xác minh không được đưa vào train. Sau đó so sánh CNN tiền huấn luyện + SVM và kết hợp nhiều bộ phận với đối chứng cùng số ảnh. Chưa huấn luyện học sâu trong bản này.

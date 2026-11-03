# Giao thức mở rộng bốn siêu tham số

Ghi trước lần chạy ngày 03/11/2026. Đây là nghiên cứu bổ sung trên dữ liệu development cũ. Tập test 194 ảnh đã được mở ở giai đoạn 2; không dùng lại để chọn hoặc xác nhận thiết kế mới.

## Mục tiêu và biến tối ưu

Giữ bộ texture128 có 126 chiều và StandardScaler fit bên trong mỗi fold. Tối thiểu hóa `1 - mean inner CV Macro-F1` với bốn biến: kernel thuộc {linear, rbf}; C log[1e-3,1e3]; gamma log[1e-5,1e-1] chỉ hoạt động với RBF; class_weight thuộc {None, balanced}. Đây là miền điều kiện bốn biến, không phải mọi lần fit đều có bốn biến hoạt động.

Đối chứng gồm SVM mặc định; Random Search ba biến; Random Search bốn biến; TPE bốn biến. Mỗi search dùng 40 trial x năm seed {11,29,47,71,101}; TPE có 10 trial khởi động, không pruning; n_jobs=1; BLAS/OMP=1. Không thêm seed/trial sau khi xem kết quả.

## Đánh giá chéo lồng nhau

Chỉ lấy 778 dòng development trong manifest đã kiểm toán. Năm outer fold theo StratifiedGroupKFold shuffle seed 2031; mỗi tập outer-train có ba inner fold theo nhóm seed 2032 + outer_fold. Mỗi fold đều kiểm tra nhóm không giao nhau. Mỗi search chỉ thấy inner-train/inner-validation trong outer-train. Outer-validation chỉ dùng để chấm cấu hình đã chọn.

Tổng 5 x 3 search x 5 seed x 40 = 3.000 trial, tương ứng 9.000 inner CV fit. Lưu cả dự đoán outer-validation từng seed để mô tả biến thiên, không chọn seed bằng outer-score.

Chính sách chính `selected4`: trong mỗi outer-train chọn baseline/Random4/TPE4 bằng trung bình best-inner-CV của năm seed; hòa ưu tiên baseline rồi Random4 rồi TPE4. Trong phương pháp được chọn, lấy cấu hình cao nhất inner-CV, hòa ưu tiên C nhỏ, số trial nhỏ, seed nhỏ. Refit outer-train rồi dự đoán outer-validation. Mỗi ảnh có đúng một dự đoán của chính sách chính.

Chỉ số chính: Macro-F1 và accuracy của các dự đoán outer OOF ghép lại. Báo recall từng loài, confusion matrix, mean/SD theo seed cho từng search và thời gian. Bootstrap ghép cặp theo nhóm là chẩn đoán có điều kiện; các mô hình outer-fold có tập train chồng lấn nên không xem khoảng đó là bằng chứng độc lập về khả năng dùng thực tế.

Quan trọng: texture128 đã được chọn trước đây bằng chính dữ liệu development này. Nested CV lần này đánh giá bước tối ưu với biểu diễn cố định trong một phân tích tiếp nối; không loại bỏ hoàn toàn sai lệch do lựa chọn biểu diễn trong lịch sử. Nhóm dữ liệu cũng chỉ dựa trên ảnh trùng/gần trùng, không phải ID cây đã được xác nhận. Chưa có tập kiểm thử ngoài miền ở Việt Nam.

## Fit mô hình bàn giao

Sau nested CV, chạy lại ba search với cùng ngân sách trên toàn bộ development và ba fold cố định cũ: thêm 600 trial/1.800 CV fit. Chọn baseline/Random4/TPE4 theo cùng quy tắc inner-CV; không sử dụng điểm outer hay test cũ để đổi lựa chọn. Fit mô hình bàn giao trên 778 dòng. Lưu riêng `models/phase3_optimized.joblib` và metadata; giữ mô hình giai đoạn 2 làm mốc lịch sử.

Tổng ngân sách HPO mới: 3.600 trial, 10.800 CV fit; baseline, refit và chẩn đoán ngoài ngân sách này được đếm riêng. Ghi giao thức JSON và hash mã/manifest trước trial đầu tiên. Dừng nếu thư mục lần chạy đã tồn tại; khi lỗi chỉ resume trạng thái đã ghi hoặc dùng run mới có giải thích, không âm thầm thay kết quả.

## Phạm vi mở rộng dữ liệu

Tích hợp bộ tiêu chuẩn 20 loài Việt Nam, ưu tiên 12 loài, vào `research/vietnam`. Xây dựng bộ kiểm tra manifest có nhãn bộ phận, nguồn, giấy phép, định danh cây/quan sát và nhóm trùng. Không coi 69 ứng viên truy hồi theo tên là nhãn đã kiểm định. Không fit nhiều bộ phận khi chưa có dữ liệu ghép thật và quyền sử dụng rõ. API bản này phục vụ ảnh lá của sáu lớp đã học, không nhận ảnh thân/rễ như thể đã huấn luyện chúng.

# Bản phát hành nghiên cứu v0.3

Ngày 03/11/2026. Mở rộng tìm kiếm SVM từ ba lên bốn biến bằng class_weight, ghi giao thức trước trial đầu tiên, chạy 3.600 trial với 10.800 inner CV fit. Đánh giá mới dùng nested grouped CV trên 778 ảnh development cũ; không chấm lại test lịch sử.

Macro-F1 nested OOF: mặc định 86,1689%, chính sách chọn bốn biến 88,0614%. Đây là kết quả của chính sách chọn cấu hình ở từng outer-train, không phải phép chấm ngoài mẫu trực tiếp của một mô hình refit duy nhất. Biểu diễn đã được chọn bằng development trong lịch sử, nên cần đánh giá ngoài miền để xác nhận ứng dụng thực tế.

TPE4 được chọn ở toàn development. Cấu hình refit: RBF, C=6.602593199343702, gamma=0.005818740333111208, class_weight=None. Bốn biến đã tham gia tìm kiếm dù giá trị trọng số thắng là None. Random3 có mean OOF theo seed cao hơn các search bốn biến; chưa chứng minh thêm biến thứ tư tốt hơn ổn định. Không đổi ngân sách để làm đẹp kết quả.

Bổ sung API cục bộ, ví dụ ảnh development có ghi công, kiểm tra ảnh đầu vào, lược đồ và bộ chặn nhập dữ liệu Việt Nam, notebook kết quả mới và hướng dẫn GitHub. Mã tái lập v0.3 chạy trong workspace riêng để giữ trọng số bàn giao. Mã trích đặc trưng lịch sử giữ nguyên hash; mô hình lịch sử và kết quả test cũ được giữ làm bằng chứng.

Chưa có mô hình nhận diện nhiều bộ phận, học sâu, phát hiện loài ngoài tập hoặc website công cộng. 69 ứng viên ảnh Việt Nam vẫn chưa hoàn thành kiểm định nhãn/quyền. Bộ kiểm tra trả ready_for_training=false đúng theo trạng thái đó.

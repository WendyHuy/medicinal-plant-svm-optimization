# Kế hoạch phát triển và đánh giá giai đoạn 2

Được ghi trước khi chạy thí nghiệm giai đoạn 2, ngày 27/10/2026.

## Câu hỏi và nguyên tắc

1. Bộ mô tả ảnh nào phù hợp với SVM trên tập development hiện có?
2. Trên bộ đặc trưng được chọn, Random Search và TPE cải thiện bao nhiêu so với SVM mặc định?
3. Cải thiện trên CV có xuất hiện trên tập test giữ riêng hay không?

Giữ nguyên `data/audit/manifest.csv` với SHA-256 `5a352a09cef2b6a84855fa1a23b64f5032f6c4c3e47e154600eec4e06f3b33ff`. Có 778 ảnh development, 194 ảnh test; 3 fold nhóm đã cố định. Không bổ sung hoặc thay đổi ảnh giữa các mô hình.

## A. Chọn đặc trưng trên development

Năm ứng viên được xác định trước:

- `v1`: HOG 96 px + HSV + LBP, 958 chiều; đối chứng ban đầu.
- `v1_no_color`: bỏ 48 chiều HSV khỏi v1, còn 910 chiều.
- `texture128`: HSV + LBP đa tỉ lệ + GLCM, 126 chiều.
- `enhanced128`: HOG 128 px + HSV + LBP đa tỉ lệ + GLCM, 1.890 chiều.
- `center128`: như enhanced128 nhưng lấy vùng trung tâm 80% chiều rộng/cao trước resize; kiểm tra giả thuyết giảm nền. Đây không phải phân đoạn lá.

LBP dùng (P,R) = (8,1), (16,2), (24,3), histogram uniform 10+18+26 chiều. GLCM dùng 32 mức xám, khoảng cách 1 và 3, góc 0/45/90/135 độ; lấy trung bình và độ lệch chuẩn theo góc của 6 thuộc tính ở từng khoảng cách, tổng 24 chiều.

Mỗi ứng viên dùng cùng SVM mặc định (RBF, C=1, gamma=scale) và 3 fold. Chọn Macro-F1 CV trung bình cao nhất; nếu hòa chọn ít chiều hơn, rồi thứ tự khai báo. Chưa sử dụng điểm test. Điểm CV này dùng để chọn mô hình, không được trình bày như đánh giá ngoài mẫu độc lập.

## B. Tối ưu cùng bộ đặc trưng đã chọn

- `StandardScaler` nằm trong pipeline, chỉ fit trên train của từng fold.
- Random Search và TPE có cùng miền: kernel {linear, rbf}, C log[1e-3,1e3], gamma log[1e-5,1e-1] khi RBF.
- 40 trial/phương pháp/seed; seed {11,29,47,71,101}; 400 trial, 1.200 CV fit, không tính giai đoạn A và baseline.
- TPE khởi động bằng 10 trial ngẫu nhiên. Không pruning, không chạy song song trial; số luồng BLAS/OMP=1.
- Mục tiêu chính: mean CV Macro-F1. Lưu điểm từng fold, thời gian, tham số và đường hội tụ.
- Chọn phương pháp bằng trung bình best-CV qua 5 seed (so với baseline). Chọn cấu hình của phương pháp đó bằng best-CV; nếu bằng nhau ưu tiên C nhỏ, rồi số trial, rồi seed. Nếu baseline có trung bình cao nhất, giữ baseline.

## C. Đóng băng trước đánh giá test

Lưu `results/final/frozen_selection.json` gồm feature ID, tham số, manifest hash và SHA-256 mã trích đặc trưng; huấn luyện/lưu mô hình trước khi trích đặc trưng test.

Một đợt chấm test gồm: pipeline v1 mặc định (tham chiếu tiến độ), SVM mặc định trên bộ đặc trưng đã chọn, cấu hình Random Search được chọn bằng CV, cấu hình TPE được chọn bằng CV. Không chọn lại mô hình theo điểm test. Cả bốn đều chỉ fit trên 778 ảnh development, không fit trên test.

Lưu accuracy, Macro-F1, balanced accuracy, precision/recall/F1 mỗi lớp, confusion matrix, train/test gap và thời gian. Phép so sánh HPO chính dùng SVM mặc định và mô hình được chọn bằng CV trên cùng bộ đặc trưng.

Dùng 2.000 lần bootstrap ghép cặp theo nhóm và phân tầng theo lớp, seed 2028, để ước lượng khoảng 95% của chênh lệch Macro-F1. Dùng kiểm định nhị thức chính xác McNemar cho chênh lệch đúng/sai; chỉ diễn giải nó cho accuracy. Không xem khoảng bootstrap là bảo đảm tổng quát trên cây/phiên chụp mới vì dữ liệu không có mã mẫu thực vật.

## D. Bàn giao và GitHub

Đưa vào báo cáo đầy đủ cả kết quả tốt và kết quả không cải thiện. Không tạo số liệu giả, không thay test để nâng điểm. GitHub chỉ sau khi hoàn thành kiểm tra và báo cáo, giữ dữ liệu thô/mô hình lớn ngoài git, có lệnh tải và tái lập. Không tạo lịch sử commit lùi ngày.

Nguồn kỹ thuật: tài liệu chính thức scikit-image (LBP, GLCM), scikit-learn (C/gamma, Pipeline, thiên lệch chọn mô hình), Optuna TPESampler. Học sâu là hướng mở rộng, chưa đưa vào thí nghiệm chính lần này.

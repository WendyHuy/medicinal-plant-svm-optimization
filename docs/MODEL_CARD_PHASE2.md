# Model card

Phân loại có giám sát ảnh lá vào sáu nhãn nguyên văn BDMediLeaves: Centella Asiatica, Justicia Adhatoda, Kalanchoe Pinnata, Mikania Micrantha, Phyllanthus Emblica, Terminalia Arjuna. Không dùng học sâu. Tên loài không tự suy ra công dụng/độ an toàn của cây.

Ảnh chuyển RGB, resize 128 × 128. HSV 48 chiều + LBP đa tỉ lệ 54 chiều + GLCM 24 chiều → StandardScaler → SVC. Toàn bộ ảnh gồm nền tham gia đặc trưng. Đầu ra là nhãn; chưa có phân đoạn, xác suất hiệu chỉnh hoặc unknown.

Huấn luyện 778 ảnh development, ba fold cố định. HPO 40 trial × 5 seed/phương pháp. Random được chọn trước test bằng trung bình best-CV qua seed. Seed 101 trial 24, RBF C=13.28777377006487, gamma=0.006029953818540779. Hai tệp models chỉ fit development; hash đi kèm.

Test 194 ảnh / 193 nhóm heuristic, chấm một đợt sau khi khóa mô hình. Macro-F1 0.830562 → 0.887053; accuracy 0.829897 → 0.886598. Khoảng bootstrap ghép cặp 95% cho delta F1 [0.020076, 0.097568], 2.000 lần phân tầng lớp/lấy mẫu nhóm. TPE test 0.891891 không được dùng để chọn lại. Xem predictions.csv để tính lại.

Dữ liệu nhỏ, không có ID cây/lá/phiên chụp; pHash không loại hết tương quan. Nhãn do nguồn cung cấp, chưa có kiểm định chuyên gia độc lập trong dự án. Chưa kiểm thử ngoài miền hoặc ngoài sáu lớp. Train F1=1 nhưng test F1≈0.887. Ảnh lạ/hỏng/nhiều lá có thể nhận nhãn sai mà không cảnh báo.

Hướng tiếp theo: thu dữ liệu theo cây/phiên chụp có nhãn kiểm định; giữ test ngoài miền trước điều chỉnh. So sánh CNN tiền huấn luyện + SVM, rồi fine-tune khi đủ dữ liệu/ngân sách. Không dùng holdout đã mở như đánh giá độc lập cho thiết kế mới.

Phục vụ học thuật, không dùng để quyết định cây ăn được hoặc điều trị. Chỉ nạp joblib từ nguồn tin cậy vì định dạng này có thể thực thi mã khi tải.

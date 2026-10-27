# Nhận diện cây dược liệu qua ảnh lá - SVM và tối ưu siêu tham số

**Giai đoạn 1: nghiên cứu và thí nghiệm thăm dò trên dữ liệu thật.**
Ngày thực hiện: 27/10/2026. Đây là học máy có giám sát: ảnh lá là đầu vào, tên loài là nhãn.

## Kết quả hiện có

- Đã tải và xác minh SHA-256 của tệp `Non Augmented Images-.zip`, BDMediLeaves 6 loài.
- 1.217 ảnh nguồn; không có ảnh lỗi; bỏ 245 bản trùng điểm ảnh, còn 972 ảnh 512 × 512.
- Phát hiện 31/121 ảnh test gốc trùng điểm ảnh với train gốc. Không dùng nguyên cách chia của nguồn.
- Chia lại theo nhóm ảnh: 778 ảnh development, 194 ảnh test giữ riêng; 3 fold cố định trên development.
- Đã chạy SVM mặc định và 120 trial HPO: 20 trial × 2 phương pháp × 3 seed.
- Macro-F1 CV: baseline 0,7521; trung bình điểm tốt nhất qua 3 seed của Random Search 0,7531 và TPE 0,7625.
- Cấu hình đơn tốt nhất: TPE seed 47, CV 0,7651. **Đây không phải độ chính xác trên test hay ngoài thực tế.**
- 6 kiểm tra tự động đã qua; có log thực nghiệm, biểu đồ, notebook và mô hình thử nghiệm đã huấn luyện.

## Bắt đầu

Python 3.12 được dùng khi kiểm chứng. Mở terminal tại thư mục chứa README này:

```bash
python -m venv .venv
```

Kích hoạt môi trường trên Windows: `.venv\Scripts\activate`; trên macOS/Linux: `source .venv/bin/activate`.

```bash
python -m pip install -r requirements.txt
python -m src.download
python -m unittest discover -s tests -v
```

Tệp nén bàn giao không chứa ảnh gốc; lệnh download tải khoảng 60 MB từ Mendeley và kiểm tra checksum. Ảnh vẫn ở giấy phép CC BY 4.0 của tác giả nguồn. Nếu nguồn từ chối tải tự động, tải **Non Augmented Images-.zip** tại [trang dữ liệu](https://data.mendeley.com/datasets/t9rns2gmr3/1), đặt tại `data/source/originals.zip`, rồi chạy lại lệnh download để kiểm tra và giải nén.

Xem kết quả đã có trong `report/`, `results/figures/`, và `notebooks/Nghien_cuu_giai_doan_1.ipynb`. Jupyter là tùy chọn; có thể mở notebook bằng VS Code hoặc cài Jupyter riêng.

Nếu dựng lại tệp báo cáo/notebook, cài thêm `requirements-artifacts.txt`. Script tạo PDF hiện dùng phông DejaVu trong `/usr/share/fonts/truetype/dejavu` trên Linux; trên hệ điều hành khác cần sửa đường dẫn phông trong `build_research_report.py`. Không cần dựng lại PDF để chạy mô hình.

## Chạy lại từ dữ liệu nguồn

Giữ nguyên manifest đã đóng băng khi so sánh kết quả. Để kiểm tra bước làm sạch có tái lập được:

```bash
python -m src.audit --images data/raw --out data/audit_recheck
```

So sánh SHA-256 của `manifest.csv` mới với `data/audit/manifest.csv`. Không sửa hoặc ghi đè manifest cũ trong một đợt so sánh.

Chạy lại đúng ngân sách pilot vào thư mục kết quả mới:

```bash
python -m src.experiment --trials 20 --out results/reproduction
```

Chương trình chỉ trích đặc trưng và chấm CV của development; không chấm test. Mỗi trial gồm 3 lần fit, tổng 363 CV fit cộng 1 lần refit cấu hình được chọn. Thời gian phụ thuộc máy. Nhật ký không có pruning hay chạy trial song song.

```bash
python -m src.predict "duong_dan/anh_la.jpg"
```

Lệnh dự đoán luôn trả về một trong 6 lớp đã học. Chưa có cơ chế nhận biết loài lạ; chỉ phục vụ thử nghiệm phân loại, không suy ra công dụng điều trị.

## Thiết kế

Ảnh RGB resize 96 × 96 → HOG 900 chiều + histogram HSV 48 chiều + LBP 10 chiều → `StandardScaler` → `SVC`.
HOG mô tả hướng cạnh, không phải phân đoạn lá chính xác. Toàn bộ ảnh, gồm nền, đang tham gia trích đặc trưng.

Không gian tìm kiếm: `kernel ∈ {linear, rbf}`, `C ∈ [1e-3, 1e3]` theo log; với RBF, `gamma ∈ [1e-5, 1e-1]` theo log. SVM mặc định: C=1, RBF, gamma=scale. TPE có 10 trial khởi động ngẫu nhiên.
Hai phương pháp dùng cùng không gian, seed {11,29,47}, dữ liệu và fold. `StandardScaler` được fit bên trong từng fold, không học thống kê từ validation hoặc test.

## Tệp cần đọc

| Tệp | Mục đích |
|---|---|
| `report/Bao_cao_nghien_cuu_giai_doan_1.md` | Báo cáo nghiên cứu có nguồn và kết quả thật |
| `data/source/dataset_metadata.json` | DOI, tác giả và giấy phép nguồn |
| `data/audit/source_manifest.csv` | Bản kê đầy đủ 1.217 ảnh nguồn |
| `data/audit/manifest.csv` | 972 ảnh đã lọc, nhóm, tập và fold cố định |
| `data/audit/exact_duplicates_removed.csv` | 245 bản trùng đã loại |
| `data/audit/near_duplicate_candidates.csv` | 1 cặp nghi trùng; đã xem trực quan và giữ cùng nhóm |
| `results/pilot/protocol.json` | Cấu hình thực nghiệm trước khi chạy |
| `results/pilot/trials.csv` | Toàn bộ 120 trial và thời gian |
| `results/pilot/summary.json` | Kết quả theo phương pháp và seed |
| `results/pilot/selected_model.joblib` | Mô hình thử nghiệm; chỉ nạp tệp joblib từ nguồn tin cậy |
| `results/verification.txt` | Kết quả 6 kiểm tra tự động |

## Giới hạn và việc tiếp theo

Đây là một pilot, chưa phải báo cáo cuối. Các seed chỉ thay đổi quá trình tìm tham số, không phải ba tập dữ liệu độc lập. pHash chỉ phát hiện một phần ảnh gần trùng; không có mã cây, lá hoặc phiên chụp để loại trừ hoàn toàn quan hệ giữa ảnh. Tên tệp có chữ `augmented` ngay trong archive do nguồn đặt là Non Augmented, nên không khẳng định đó là ảnh thô từ camera.

Tiếp theo: phân tích lỗi bằng dự đoán ngoài fold trên development; kiểm tra ảnh cùng phiên chụp; so sánh bỏ đặc trưng màu hoặc tách vùng lá trên development; sau đó chốt thiết kế và ngân sách trước khi đánh giá 194 ảnh test đúng một đợt. Khi mở rộng sang CNN, giữ ảnh, nhãn và manifest; thay bộ trích đặc trưng hoặc fine-tune một mô hình học sâu. Không dùng điểm test hiện tại để liên tục sửa mô hình.

Chưa tạo kho GitHub công khai, chưa có lịch sử 5 tuần và chưa có kết quả học sâu. Không tạo commit lùi ngày. Có hỗ trợ AI trong nghiên cứu, viết mã và kiểm tra; người thực hiện cần tự đọc, chạy lại và giải thích phương pháp khi nộp bài.

## Ghi nguồn dữ liệu

Islam, Saiful và cộng sự (2023), **BDMediLeaves**, Mendeley Data, V1, DOI [10.17632/t9rns2gmr3.1](https://doi.org/10.17632/t9rns2gmr3.1), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
Thay đổi trong nghiên cứu này: loại ảnh trùng điểm ảnh, gán nhóm gần trùng, chia lại development/test và trích đặc trưng. Không hàm ý tác giả dữ liệu bảo chứng kết quả này.

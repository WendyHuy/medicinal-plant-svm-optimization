# Tối ưu bốn siêu tham số SVM nhận diện cây dược liệu

Báo cáo toàn bộ dự án và bản bàn giao v0.3

Huỳnh Gia Huy  |  MSSV 2474802010135
Đại học Văn Lang  |  Chuyên ngành Trí tuệ nhân tạo
Ngày hoàn thiện 03/11/2026

### Kết quả chính

Dự án đã hoàn thành mô hình phân loại có giám sát ảnh lá của sáu loài BDMediLeaves, mở rộng miền tìm kiếm từ ba lên bốn siêu tham số và chuẩn bị nền dữ liệu cho cây dược liệu ở Việt Nam. Đánh giá bổ sung dùng nested CV theo nhóm trên 778 ảnh development cũ: Macro-F1 của SVM mặc định là 86,17% và chính sách chọn cấu hình bốn tham số là 88,06%. Mức tăng là +1,89 điểm phần trăm.

| Đánh giá nested OOF trên 778 ảnh | Mặc định | Chính sách 4 tham số |
| --- | --- | --- |
| Macro-F1 | 86,17% | 88,06% |
| Accuracy | 86,12% | 88,05% |
| Số ảnh đúng | 670 | 685 |

Nested OOF là dự đoán ở vòng ngoài, khi ảnh đó không tham gia fit hoặc tìm siêu tham số của mô hình tương ứng. Kết quả này là phân tích tiếp nối có điều kiện theo biểu diễn và dữ liệu cũ; chưa phải đánh giá trên ảnh Việt Nam ngoài nguồn.

### Phạm vi đã hoàn thành

Bản bàn giao có mô hình đã học, CLI, API ảnh lá, nhật ký 3.600 trial, dự đoán OOF, ma trận nhầm lẫn, notebook, kiểm tra tự động và hướng dẫn GitHub. Bộ tiêu chuẩn dữ liệu Việt Nam gồm 20 ứng viên, ưu tiên 12 loài. Mô hình hiện tại vẫn nhận diện sáu lớp ảnh lá; chưa huấn luyện thân, rễ hoặc mô hình học sâu.

## 1 Bài toán và mục tiêu tối ưu

Một ảnh lá có thể khó phân biệt do hình dạng tương tự giữa các loài, ánh sáng và nền chụp. Dự án bắt đầu từ đặc trưng màu và kết cấu thủ công để có mô hình nhẹ, chạy CPU và dễ kiểm chứng. Tối ưu siêu tham số là phần trọng tâm của bài tập Python; API chỉ là lớp tích hợp.

### Hàm mục tiêu

Tìm x làm nhỏ nhất f(x) = 1 - mean inner CV Macro-F1. Macro-F1 là trung bình F1 của sáu lớp, trong đó F1 = 2TP/(2TP+FP+FN). StandardScaler được fit riêng trong mỗi tập train, sau đó biến đổi tập validation tương ứng.

| Biến | Miền tìm kiếm | Ý nghĩa |
| --- | --- | --- |
| kernel | linear hoặc rbf | Dạng kernel |
| C | log từ 0,001 đến 1.000 | Mức phạt lỗi |
| gamma | log từ 0,00001 đến 0,1 | Chỉ hoạt động với RBF |
| class_weight | None hoặc balanced | Trọng số lớp |

Gamma là biến có điều kiện. Vì vậy miền có bốn biến khai báo nhưng nhánh linear không dùng gamma. class_weight=None là một kết quả hợp lệ của tìm kiếm, không có nghĩa chưa tìm tham số thứ tư. balanced điều chỉnh trọng số theo tần suất lớp trong tập train từng fold [2].

### Các đối chứng

SVM mặc định dùng RBF, C=1, gamma=scale, class_weight=None. Random3 tìm kernel, C và gamma. Random4 và TPE4 thêm class_weight. Mỗi search chạy 40 trial cho mỗi seed; TPE có 10 trial khởi động ngẫu nhiên. Không dùng số seed hoặc số trial để thay thế số siêu tham số của mô hình.

Không giả định bốn tham số luôn tốt hơn ba. Miền lớn hơn với cùng ngân sách mỗi search có thể phân bổ ít thử nghiệm hơn cho một vùng tốt. Kết luận phải dựa trên các đối chứng và sự biến thiên được ghi lại.

## 2 Dữ liệu và kiểm toán

Nguồn ảnh đã huấn luyện là BDMediLeaves V1 sáu loài, DOI 10.17632/t9rns2gmr3.1, công bố CC BY 4.0 [1]. Ảnh được thu thập ở Bangladesh. Có mặt một loài trong nghiên cứu không tự chứng minh bộ ảnh đại diện cho cách chụp hoặc điều kiện ở Việt Nam.

| Bước kiểm toán | Số lượng |
| --- | --- |
| Ảnh đọc được từ archive | 1217 |
| Bản trùng pixel đã bỏ | 245 |
| Ảnh sau lọc trùng | 972 |
| Nhóm trùng hoặc gần trùng | 971 |
| Development cho đợt mới | 778 |
| Test lịch sử đã mở | 194 |

Cách chia nguồn có rò rỉ: 31/121 ảnh test gốc trùng ảnh train gốc. Dự án chia lại sau khi lọc trùng. pHash dưới phép quay/lật nhận diện thêm một cặp gần trùng; cặp được giữ cùng nhóm. Không có mã cây, lá hay phiên chụp thật, nên nhóm vẫn chỉ là heuristic.

| Lớp nguồn | Ảnh duy nhất | Development | Test lịch sử |
| --- | --- | --- | --- |
| Centella asiatica | 164 | 132 | 32 |
| Justicia adhatoda | 162 | 130 | 32 |
| Kalanchoe pinnata | 162 | 129 | 33 |
| Mikania micrantha | 160 | 128 | 32 |
| Phyllanthus emblica | 157 | 125 | 32 |
| Terminalia arjuna | 167 | 134 | 33 |

Archive mang tên Non Augmented nhưng có tên ảnh chứa augmented; không khẳng định đây là toàn bộ ảnh camera chưa xử lý. Mã băm archive, từng file và manifest được lưu. Đợt này chỉ trích đặc trưng development, không chấm lại 194 ảnh test.

## 3 Đặc trưng và kiến trúc mô hình

Pipeline là ảnh RGB resize 128 x 128, trích HSV + LBP đa tỉ lệ + GLCM, chuẩn hóa StandardScaler và SVC. Mỗi vector có 126 chiều. Trích đặc trưng chỉ phụ thuộc một ảnh, không học thống kê từ toàn bộ dataset.

| Thành phần | Thiết lập | Số chiều |
| --- | --- | --- |
| HSV | 16 bin cho mỗi kênh H S V | 48 |
| LBP uniform | (P,R) = (8,1), (16,2), (24,3) | 54 |
| GLCM | 32 mức xám; khoảng cách 1 và 3; bốn góc | 24 |
| Tổng | texture128 | 126 |

GLCM dùng contrast, dissimilarity, homogeneity, energy, correlation và ASM; lấy trung bình/độ lệch chuẩn qua góc. Bộ texture128 được chọn ở giai đoạn 2, không có HOG. Nền ảnh vẫn tham gia đặc trưng.

### Kết quả chọn đặc trưng trong lịch sử

| Bộ mô tả | Số chiều | Macro-F1 CV |
| --- | --- | --- |
| v1 HOG HSV LBP | 958 | 75,21% |
| v1 bỏ màu | 910 | 71,50% |
| texture128 | 126 | 85,63% |
| enhanced128 có HOG | 1890 | 78,04% |
| crop giữa 80 phần trăm có HOG | 1890 | 78,50% |

Biểu diễn texture128 đã được chọn bằng development trước đây. Do đó nested CV mới chỉ đánh giá tối ưu siêu tham số khi giữ biểu diễn này cố định; không xóa sai lệch lịch sử do chọn đặc trưng. Trong test lịch sử, v1 và texture128 mặc định đạt Macro-F1 gần nhau 82,96% và 83,06%; mức tăng CV không được suy thành mức tăng test tương ứng.

## 4 Thiết kế thực nghiệm bổ sung

Giao thức PHASE3_PROTOCOL.md và protocol.json được ghi trước trial đầu tiên, kèm hash mã, manifest và phiên bản thư viện. Outer CV gồm năm fold phân tầng theo nhóm, seed 2031; mỗi outer-train có ba inner fold theo nhóm, seed 2032 cộng số fold. Mọi nhóm được kiểm tra không giao nhau giữa train và validation [3].

| Phạm vi | Search | Ngân sách HPO |
| --- | --- | --- |
| Mỗi outer fold | Random3 Random4 TPE4 | 3 x 5 seed x 40 trial |
| Năm outer fold | Tổng nested CV | 3.000 trial / 9.000 CV fit |
| Toàn development | Ba search như trên | 600 trial / 1.800 CV fit |
| Tổng mới | Không tính baseline và refit | 3.600 trial / 10.800 CV fit |

Năm seed cố định là 11, 29, 47, 71 và 101. Chạy tuần tự với n_jobs=1 và một luồng BLAS/OMP; không pruning. Các seed dùng cùng dữ liệu, không phải năm bộ dữ liệu độc lập. Baseline có thêm 18 CV fit; các mô hình outer và mô hình cuối có 86 refit.

### Quy tắc chọn cấu hình

Trong từng outer-train, tính mean best-inner-CV qua năm seed của Random4 và TPE4, có so baseline. Chọn phương pháp cao nhất, hòa ưu tiên baseline rồi Random4 rồi TPE4. Trong phương pháp đó chọn cấu hình cao nhất inner-CV, hòa ưu tiên C nhỏ, trial nhỏ rồi seed nhỏ. Outer-validation không được dùng để chọn.

Chính sách selected4 thực hiện cùng quy tắc ở cả năm outer fold. Sau đánh giá, lựa chọn mô hình bàn giao được tính lại trên toàn development theo ba fold cố định cũ; không dùng outer-score hoặc test cũ để đổi lựa chọn.

Đây là phân tích tiếp nối, không phải đăng ký nghiên cứu độc lập. Tập test cũ giữ vai trò kết quả lịch sử. Cần tập ảnh mới và mã cá thể thật để đánh giá khả năng dùng ngoài nguồn.

## 5 Kết quả tìm kiếm và độ ổn định

Hình 1 Macro-F1 nested OOF. Thanh sai số ở ba search là SD giữa năm seed; hai chính sách còn lại có một bộ dự đoán OOF.

| Đối chứng | Mean OOF Macro-F1 | SD giữa seed |
| --- | --- | --- |
| Random3 | 87,80% | 0,42 điểm % |
| Random4 | 86,36% | 2,44 điểm % |
| TPE4 | 87,29% | 0,83 điểm % |

Random3 có mean theo seed cao hơn cả Random4 và TPE4 trong thí nghiệm này. Random4 có độ biến thiên lớn nhất. Vì vậy chưa có bằng chứng rằng thêm class_weight làm chất lượng tăng ổn định ở cùng ngân sách mỗi search.

Chính sách selected4 chọn TPE4 ở cả năm outer fold và đạt OOF cao hơn baseline. Chính sách này chọn qua năm seed và hai search bốn biến; không so trực tiếp nó với một seed Random3 như thể có cùng tổng ngân sách. Thứ hạng này không chứng minh phương pháp nào luôn tốt hơn trên dữ liệu khác.

## 6 So sánh trước và sau tối ưu

| Chỉ số nested OOF | Baseline | Selected4 |
| --- | --- | --- |
| Macro-F1 | 86,17% | 88,06% |
| Accuracy | 86,12% | 88,05% |
| Đúng trên 778 ảnh | 670 | 685 |
| Sai trên 778 ảnh | 108 | 93 |

Hình 2 Ma trận nhầm lẫn của chính sách selected4 trên các dự đoán outer OOF

So với baseline, selected4 sửa 34 lỗi nhưng phát sinh 19 lỗi mới, tăng ròng 15 ảnh đúng. Không chỉ báo số lỗi đã sửa mà bỏ qua lỗi mới.

Bootstrap ghép cặp theo nhóm 2.000 lần cho khoảng chẩn đoán delta Macro-F1 [+0,09; +3,68] điểm phần trăm. Các tập train outer chồng lấn, biểu diễn đã được chọn trên development và nhóm là heuristic; khoảng này không là bảo đảm độc lập cho ảnh cây mới.

## 7 Phân tích từng loài và lỗi còn lại

| Loài | F1 trước | F1 sau | Recall sau |
| --- | --- | --- | --- |
| Centella Asiatica | 85,19% | 87,18% | 90,15% |
| Justicia Adhatoda | 81,54% | 83,92% | 82,31% |
| Kalanchoe Pinnata | 92,91% | 96,12% | 96,12% |
| Mikania Micrantha | 81,82% | 83,52% | 85,16% |
| Phyllanthus Emblica | 87,10% | 89,16% | 88,80% |
| Terminalia Arjuna | 88,46% | 88,46% | 85,82% |

Hình 3 F1 từng lớp trên cùng các dự đoán nested OOF

Kalanchoe có F1 cao nhất trong vòng đánh giá này. Justicia và Mikania còn nhiều nhầm lẫn. Terminalia không tăng F1 dù một số dự đoán thay đổi. Các cặp sai nổi bật gồm Terminalia sang Mikania 9 ảnh, Justicia sang Centella 8 ảnh, Centella sang Justicia 7 ảnh và Terminalia sang Justicia 7 ảnh.

Đây là mô tả lỗi trên dữ liệu hiện tại; chưa xác minh cơ chế gây nhầm. Màu, nền và trạng thái lá là các giả thuyết cần thử bằng dữ liệu khác nguồn và thử nghiệm tách biệt, không kết luận từ ma trận nhầm lẫn đơn thuần.

## 8 Mô hình bàn giao và kết quả lịch sử

Mô hình bàn giao được chọn bằng inner-CV trên toàn development: tpe4, seed 11, trial 14. Tham số cuối là kernel=rbf, C=6.60259320, gamma=0.00581874, class_weight=None. Mô hình fit trên 778 ảnh; train Macro-F1 99,87%. Train-score cao không thay thế đánh giá ngoài mẫu.

Hình 4 Best inner CV trên toàn development. Đường là mean và vùng tô là SD giữa năm seed, không phải test-score.

| Đánh giá test lịch sử 194 ảnh | Macro-F1 | Accuracy |
| --- | --- | --- |
| Baseline 126 chiều | 83,06% | 82,99% |
| Random3 chọn ở giai đoạn 2 | 88,71% | 88,66% |
| TPE3 đối chứng | 89,19% | 89,18% |

Bảng test lịch sử giữ nguyên kết quả đã công bố; mô hình v0.3 chưa được chấm lại trên 194 ảnh này. Không ghép 88,71% test cũ và 88,06% nested OOF mới thành một phép so sánh tăng/giảm vì khác tập và giao thức.

class_weight=None được tìm ra trong miền bốn biến. Dữ liệu sáu lớp gần cân bằng nên không kỳ vọng balanced mặc định tốt hơn. Không chứng minh riêng tác động của cân bằng lớp chỉ từ cấu hình thắng.

## 9 Mở rộng dữ liệu cây dược liệu Việt Nam

Nghiên cứu Việt Nam hiện có 20 ứng viên, ưu tiên 12 loài. Đã đọc metadata Viet Medi Species: 4.799 dòng, trong đó 4.667 thực vật; cả 20 ứng viên có dòng tên tương ứng. Thống kê repo phân biệt danh mục loài với loài có ảnh, nên không coi mọi dòng metadata là một lớp ảnh sẵn sàng [5].

| Mã | Loài ưu tiên | Tên khoa học mục tiêu |
| --- | --- | --- |
| VN001 | Rau má | Centella asiatica |
| VN002 | Diếp cá | Houttuynia cordata |
| VN003 | Tía tô | Perilla frutescens |
| VN004 | Húng chanh | Coleus amboinicus |
| VN005 | Lá lốt | Piper sarmentosum |
| VN006 | Trầu không | Piper betle |
| VN007 | Lô hội | Aloe vera |
| VN008 | Thuốc bỏng | Kalanchoe pinnata |
| VN009 | Cỏ nhọ nồi | Eclipta prostrata |
| VN010 | Xuyên tâm liên | Andrographis paniculata |
| VN011 | Ích mẫu | Leonurus japonicus |
| VN012 | Râu mèo | Orthosiphon aristatus |

Nhóm mở rộng là gừng, nghệ vàng, sả chanh, ổi, dâu tằm, bụp giấm, đậu biếc và chùm ngây. Ngải cứu, bạc hà, diệp hạ châu, mã đề và cà gai leo chờ xác minh danh pháp và ảnh dễ nhầm. Tên Việt không dùng làm khóa loài duy nhất.

TDTU VQA có 29.151 cặp hỏi đáp nhưng chỉ 3.790 đường dẫn ảnh. Lọc tên chính xác ra 69 ứng viên. Sàng lọc 18 ảnh có chủ đích phát hiện 8 ảnh nghi không khớp nhãn và một cặp trùng byte mang hai nhãn; không suy tỷ lệ lỗi cho toàn bộ dataset. Chưa có ảnh nào hoàn thành đủ định danh và quyền sử dụng [6].

## 10 Nhiều bộ phận và nền tảng tích hợp

Mỗi quan sát tương lai phải gắn các ảnh với cùng cây/khóm và lần chụp: mặt trên lá, mặt dưới lá, thân/đốt và toàn cây. Hoa/quả bổ sung khi có. Thân rễ của gừng/nghệ phân biệt với rễ. Tuổi chỉ ghi khi có nhật ký gieo/trồng; không suy số tháng tuổi từ ảnh. Observation ID không tự chứng minh các phiên khác nhau là các cá thể khác nhau [7].

### Kiểm tra trước khi nhập dữ liệu

Mô đun curation tạo bản ghi nhãn và kiểm tra schema, trạng thái định danh, người rà soát, giấy phép, ghi công, nhóm trùng, hash ảnh, rò rỉ theo cây/quan sát và việc ghép ảnh khác cây. Chạy trên 69 ứng viên hiện tại: cấu trúc hợp lệ nhưng ready_for_training=false, 0 train_keep và 0 quan sát nhiều bộ phận được xác minh. Đây là chặn đúng, không phải lỗi cần bỏ qua.

### API và CLI

CLI mặc định dùng phase3_optimized.joblib. API có GET /health và POST /predict cho ảnh JPEG/PNG/WEBP, giới hạn 10 MB và 20 triệu pixel. API xác minh hash mô hình và đặc trưng, xử lý file tạm rồi xóa; không lưu ảnh tải lên. API từ chối khai báo organ khác leaf; người dùng vẫn cần gửi đúng loại ảnh vì hệ thống chưa tự phát hiện cơ quan.

Đầu ra gồm nhãn trong sáu lớp và ba ứng viên kèm decision score của SVM. Điểm này chưa hiệu chỉnh, không phải xác suất đúng. Chưa có bộ phát hiện loài lạ; ảnh ngoài sáu lớp vẫn có thể bị gán vào một lớp đã biết. API hiện phù hợp demo nghiên cứu và tích hợp cục bộ [8].

### Website phổ cập kiến thức

Kho tri thức có thể gồm tên chuẩn/tên địa phương, hình thái, giai đoạn, phân bố và cây dễ nhầm với nguồn riêng. Công dụng cần phân biệt bằng chứng truyền thống, tiền lâm sàng và lâm sàng, có rà soát chuyên môn. Không lấy nguyên QA chưa kiểm chứng để tạo hướng dẫn điều trị. Chưa phát hành website công cộng trong bản này.

## 11 Kiểm chứng bàn giao và tài liệu tham khảo

Bộ kiểm tra hiện có 25 test; 21 chạy đạt và 4 bỏ qua có lý do vì cache/trọng số thí nghiệm lịch sử không đưa vào Git. Các kiểm tra mới gồm đủ ngân sách, tính lại F1 từ OOF, tách nhóm, lựa chọn chỉ theo inner-CV, hash mô hình, chặn nhãn chưa kiểm định, chặn ghép khác cây và API với ảnh thật. CI được cấu hình để chạy sau khi người dùng push; chưa có kết quả CI từ GitHub.

Thời gian đo lần này: trích đặc trưng development 18.74 giây; tìm kiếm/đánh giá bổ sung 201.04 giây, không gồm tải dữ liệu. Mô hình mới 352,407 byte. Các số này thuộc CPU môi trường thực nghiệm, không cam kết trên máy cá nhân.

### Tái lập và đưa lên GitHub

Cài Python 3.12, tạo venv, cài requirements-api.txt. Chạy python -m unittest discover -s tests -v; dự đoán bằng python -m src.predict examples/centella_development.jpg --compare; mở API bằng python -m uvicorn src.service:app --host 127.0.0.1 --port 8000. Hướng dẫn tái lập nằm trong README; dùng thư mục kết quả mới để bảo toàn nhật ký.

Bản ZIP có mã, trọng số, báo cáo, dữ liệu kiểm toán và lịch sử Git dạng bundle; không có raw archive hoặc môi trường ảo. Tạo repo của người dùng rồi push theo docs/GITHUB_UPLOAD.md. Commit giữ ngày thực tế; lịch sử vài ngày không thay thế yêu cầu làm bài trong năm tuần. Có hỗ trợ AI; sinh viên cần tự chạy và hiểu phương pháp trước khi nộp.

### Tài liệu tham khảo

[1] Islam và cộng sự. BDMediLeaves V1. Mendeley Data 2023. DOI 10.17632/t9rns2gmr3.1. CC BY 4.0.

[2] scikit-learn. SVC API. https://scikit-learn.org/stable/modules/generated/sklearn.svm.SVC.html

[3] scikit-learn. Nested versus non-nested cross-validation. https://scikit-learn.org/stable/auto_examples/model_selection/plot_nested_cross_validation_iris.html

[4] Optuna. TPESampler 4.5.0. https://optuna.readthedocs.io/en/v4.5.0/reference/samplers/generated/optuna.samplers.TPESampler.html

[5] Tran và cộng sự. Viet Medi Species 2026. DOI 10.57760/sciencedb.013q9. Repo github.com/trientran/VietMediSpecies nhánh feature/update.

[6] azan100an. TDTU VQA Herb. huggingface.co/datasets/azan100an/tdtu_vqa_dataset_herb. CC BY-NC 4.0; quyền ảnh gốc cần kiểm tra.

[7] LifeCLEF 2014 Plant Task. https://www.imageclef.org/2014/lifeclef/plant

[8] FastAPI. Request files và Testing. https://fastapi.tiangolo.com/tutorial/

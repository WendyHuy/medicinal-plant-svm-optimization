# Quy tắc chọn dữ liệu cho nhận diện cây dược liệu ở Việt Nam

Phiên bản 0.1 — ngày 29/10/2026. Đây là thiết kế nghiên cứu mới; chưa phải bản dữ liệu đã đủ điều kiện huấn luyện.

## 1. Quyết định về nguồn

- Ưu tiên kiểm kê ảnh gốc có provenance của Viet Medi Species/GBIF và nguồn tự chụp có định danh. Lọc về thực vật và 20 loài ưu tiên. Mỗi ảnh cần URL, người tạo, giấy phép và mã bản ghi gốc.
- TDTU VQA chỉ dùng để tìm ứng viên và nghiên cứu cách mô tả. Ảnh/QA cần rà soát toàn bộ khi sử dụng: đã tìm thấy cặp nhãn–ảnh không phù hợp và ảnh cùng byte mang hai nhãn khác nhau. Không dùng trực tiếp QA làm nội dung website hoặc nhãn hình thái.
- VNPlant-200 là nguồn chờ xác minh quyền truy cập, danh sách nhãn, giấy phép và cá thể/lần chụp. Chưa tính 20.000 ảnh công bố là ảnh đã có trong bộ sạch.
- TCMP-300 và các bộ lá quốc tế chỉ nhập sau đối chiếu tên khoa học, loài có ở Việt Nam, quyền sử dụng và ảnh trùng liên nguồn. Không ghép dữ liệu chỉ vì cùng tên Việt.

## 2. Ảnh giữ cho bài toán chính

Giữ ảnh màu của cây sống, hoặc lá tươi tách rời trong nhánh thí nghiệm lá. Có thể thấy rõ một bộ phận đặc trưng, không cần nền trắng. Ưu tiên cạnh ngắn từ 512 px, cho phép từ 224 px khi vẫn thấy đặc điểm; đây là ngưỡng vận hành dự kiến, cần điều chỉnh theo kiểm kê ảnh gốc. Không phóng ảnh nhỏ lên để tính thành ảnh đủ độ phân giải.

Mỗi cá thể/lần quan sát ưu tiên bốn góc: mặt trên lá, mặt dưới lá, thân–đốt/cách mọc lá và toàn cây. Hoa/quả bổ sung khi có. Với cây dạng hoa thị hoặc không lộ thân, ghi bộ phận thiếu và chụp gốc/bẹ phù hợp; không ép mọi loài đủ cùng bộ phận. Một ảnh có thể chứa nhiều bộ phận.

Giữ biến thiên thật về ánh sáng vừa phải, nền, giống trồng, lá non/già, màu xanh/tía và tổn thương nhẹ nếu danh tính vẫn xác định được. Không chỉ giữ những ảnh đẹp hoặc cây trưởng thành. Nếu màu sắc là đặc điểm nghiên cứu, tránh tăng cường màu quá mạnh làm mất đặc điểm thật.

## 3. Ảnh cách ly, loại và dành riêng

| Quyết định | Trường hợp |
|---|---|
| Cách ly chờ xác minh | Tên mơ hồ; ảnh khác mô tả; nhãn nguồn mâu thuẫn; thiếu quyền; không rõ cây chính; gán tuổi theo suy đoán |
| Loại khỏi bộ chính | Hỏng file; mờ nặng; che gần hết bộ phận; ảnh chữ/bao bì/sản phẩm; đối tượng ngoài thực vật |
| Giữ một bản đại diện | Trùng byte/pixel; ảnh xoay/lật/cắt từ cùng ảnh; các bản còn lại lưu quan hệ trùng, không xóa dấu vết |
| Bộ tư liệu riêng | Hình vẽ, ảnh ghép, tiêu bản, bột/dược liệu khô/chế biến; ảnh rễ/thân rễ tách rời chưa gắn được với cá thể |
| Thử thách riêng | Loài ngoài danh sách, cây dễ nhầm, ảnh nhiều loài và ảnh chất lượng kém để thử khả năng từ chối |

Ảnh có watermark cần xem xét quyền và nguy cơ học logo. Không tự xóa watermark. Nếu được phép dùng, kiểm tra tác động bằng tập đánh giá khác nguồn; tránh để mỗi loài gắn độc quyền một logo/nền chụp.

## 4. Nhãn phải giữ

Lược đồ máy đọc nằm ở `annotation_schema.json`. Danh mục loài và tên đồng nghĩa tại `species_policy.json`.

| Nhóm | Trường cần giữ | Quy tắc |
|---|---|---|
| Loài | species_id, tên gốc, tên khoa học, nguồn/phiên bản phân loại, trạng thái người rà soát | Dùng mã ổn định; tên Việt để hiển thị, không phải khóa ghép dữ liệu |
| Nguồn | source_record_id, URL, tác giả, giấy phép, ghi công | Ảnh xuất hiện ở nhiều website vẫn có thể là một ảnh gốc |
| Nhóm ảnh | plant_id, observation_id, session_id, duplicate_group_id | Không tạo plant_id giả từ tên file hoặc tên loài |
| Bộ phận | leaf, stem, bark, flower, fruit, seed, root, rhizome | Đa nhãn theo phần nhìn thấy. Thân rễ của gừng/nghệ không gán thành rễ |
| Góc chụp | leaf_upper, leaf_lower, stem_node, whole_plant... | Toàn cây là góc chụp, không phải một cơ quan thực vật |
| Trạng thái mẫu | living_plant, fresh_detached, dried, processed, herbarium, illustration | Phân biệt trước khi chọn đầu vào mô hình |
| Sinh trưởng | vegetative_stage, các phenophase nhìn thấy | Hoa/quả/nụ là bằng chứng quan sát; không tự suy cây bao nhiêu tháng tuổi |
| Tuổi | age_days, age_evidence | Không có nhật ký gieo/trồng: null, không dùng 0 thay cho không biết |
| Hình thái | hình phiến lá, mép lá, cách mọc lá, màu từng mặt/thân | Chỉ gán cái nhìn thấy; mặt dưới không có ảnh: unknown |
| Chất lượng | quyết định, lý do, trạng thái xác minh, split | Mọi thay đổi nhãn phải có dấu vết |

Không dùng tên khoa học, tên cây, đoạn mô tả chứa tên cây hoặc đáp án làm đầu vào nhận diện hình ảnh. Không điền đặc điểm từ hồ sơ loài cho mọi ảnh rồi đánh giá như thể mô hình nhìn thấy đặc điểm đó: đây là rò rỉ thông tin nhãn. Mùi, vị, hóa chất và công dụng không thể gán là quan sát ảnh.

## 5. Loài ưu tiên và điều kiện được vào huấn luyện

Chọn 12 loài ưu tiên 1 và 8 loài mở rộng ở `species_policy.json`. Đó là danh sách cần thu thập; việc có tên trong metadata chưa bảo đảm có ảnh sạch. Các loài khó phân định tên được chờ riêng, không trộn vào nhãn “cây thuốc khác”.

Mục tiêu thí điểm là 30–50 nhóm cá thể/khóm độc lập mỗi loài, mỗi nhóm khoảng bốn góc. Với 12 loài tương ứng khoảng 1.440–2.400 ảnh. Đây là mục tiêu thu thập do dự án đề xuất, không phải ngưỡng bảo đảm độ chính xác. Chụp nhiều ảnh cùng cây không thay thế việc có nhiều cá thể. Cây sinh dưỡng tạo thảm/khóm dùng plot/khóm/chậu làm nhóm thận trọng; không tự gọi các chồi trong cùng khóm là độc lập.

Nếu dữ liệu công khai thiếu định danh cá thể, chỉ dùng cho thí nghiệm một ảnh có giới hạn hoặc chuẩn bị biểu diễn. Đánh giá nhiều bộ phận của cùng cây cần quan sát ghép thật và tập kiểm tra cá thể độc lập. Có thể thu thập ít loài hơn khi chưa đủ nguồn lực, nhưng phải công bố phạm vi đúng với dữ liệu.

## 6. Chia tập và so sánh tối ưu

1. Rà soát định danh, quyền, trùng/ảnh gần trùng trước; mọi phiên chụp của cùng cây/khóm phải cùng nhóm.
2. Dự kiến 80% nhóm phát triển, 20% nhóm kiểm tra, phân tầng theo loài; ba fold theo nhóm trong tập phát triển. Khi số nhóm ít phải báo rõ độ bất định và điều chỉnh thiết kế trước khi khóa tập kiểm tra.
3. Giữ một tập ngoài nguồn huấn luyện, ưu tiên ảnh tự chụp tại Việt Nam, để đánh giá khả năng dùng trên website. Loài có ở Việt Nam và ảnh chụp ở Việt Nam là hai trường khác nhau.
4. So sánh mô hình lá cơ sở; bộ trích đặc trưng mới chỉ dùng lá; nhiều ảnh lá; nhiều bộ phận cùng số ảnh; kết hợp điểm đều; tối ưu trọng số kết hợp. Chỉ so trước/sau trên cùng tập và cùng ngân sách tìm kiếm.
5. Huấn luyện/hiệu chỉnh xác suất/đặt ngưỡng/tối ưu trọng số chỉ trên tập phát triển. Kiểm thử tình huống thiếu bộ phận. Không yêu cầu đủ hoa/quả để đưa dự đoán.
6. Báo Macro-F1, accuracy, recall từng loài, ma trận nhầm, khoảng tin cậy theo nhóm, thời gian xử lý gồm trích đặc trưng và bộ phân loại. Đánh giá khả năng từ chối bằng mẫu ngoài danh sách đã tách phù hợp; không coi softmax cao là xác suất đúng được bảo đảm.

## 7. Dữ liệu kiến thức cho website

Mỗi bài cây có tên chuẩn và tên địa phương, đặc điểm từng bộ phận, biến thiên theo giai đoạn, cây dễ nhầm, phân bố và nguồn. Nội dung hình thái điển hình lưu ở hồ sơ kiến thức; không dùng thay nhãn quan sát trong ảnh.

Phần công dụng cần ghi loại bằng chứng và nguồn riêng, có rà soát chuyên môn. Không tự chuyển câu trả lời từ VQA thành hướng dẫn dùng thuốc hoặc liều dùng. Dữ liệu website và dữ liệu được phép dùng trong nghiên cứu có thể có quyền khác nhau; giữ trạng thái quyền riêng. Chỉ đăng ảnh có đủ căn cứ sử dụng và ghi công.

## 8. Bước thực hiện kế tiếp

Lấy bảng ảnh theo từng loài từ archive/GBIF với mã bản ghi và giấy phép; kiểm tra khả năng ghép thật theo quan sát; bổ sung ảnh tại Việt Nam cho những loài thiếu. Chốt manifest có kiểm định trước khi huấn luyện. Giữ bản nghiên cứu này và kết quả cũ để làm mốc, không ghi đè mô hình đã đánh giá.

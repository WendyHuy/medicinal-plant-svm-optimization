# Nghiên cứu lựa chọn ảnh, nhãn và loài cây dược liệu ở Việt Nam

**Người thực hiện:** Huỳnh Gia Huy — MSSV 2474802010135  
**Ngày:** 29/10/2026  
**Trạng thái:** đã kiểm kê metadata và sàng lọc ảnh mẫu; chưa phát hành bộ ảnh sạch hoặc huấn luyện mô hình mới.

## 1. Quyết định nghiên cứu

Chọn **20 loài để ưu tiên thu thập**, chia thành **12 loài triển khai trước** và **8 loài mở rộng**. Chỉ đưa từng loài vào huấn luyện sau khi đủ ảnh hợp lệ, nhãn được xác minh và có tập kiểm tra phù hợp. Hiện chưa có loài nào trong đợt này được xác nhận đã đủ dữ liệu sạch.

Đầu vào chính là ảnh cây sống: lá, thân/cách mọc lá, toàn cây; hoa/quả bổ sung khi có. Rễ và thân rễ là nhánh bổ sung có nguồn gốc rõ. Bài toán tối ưu là chọn cách kết hợp những thông tin này và đánh giá khi thiếu bộ phận. Website về sau dùng cùng danh mục loài nhưng có kho kiến thức được rà soát riêng.

## 2. Việc đã kiểm tra thực tế

### 2.1. Viet Medi Species

Đã tải và đọc tệp metadata 2.519.034 byte từ repo tác giả:

| Nội dung kiểm kê | Kết quả |
|---|---:|
| Dòng metadata | 4.799 |
| Thực vật Plantae | 4.667 |
| Nấm, Chromista và Bacteria | 132 |
| Thực vật có trạng thái ACCEPTED trong bản metadata | 4.596 |
| Thực vật có trạng thái DOUBTFUL | 71 |
| Loài ứng viên của dự án tìm thấy trong metadata | 20/20 |

Danh sách 20 ứng viên đều có dòng phân loại ACCEPTED trong bản đã đọc. Đây là trạng thái của metadata nguồn, chưa phải chứng nhận đúng loài cho từng ảnh.

**Điều chỉnh lại cách hiểu số liệu công bố:** tệp `image_statistics.json` của repo ghi 310.647 ảnh thuộc 3.570 loài có ảnh; phần thực vật là 297.320 ảnh thuộc 3.450 loài. Trong khi metadata có 4.799 dòng/4.667 thực vật. Vì vậy, không coi 4.799 hoặc 4.667 là số lớp ảnh đã sẵn sàng huấn luyện. Chưa tải archive để giải quyết khác biệt giữa mô tả trang phát hành và thống kê repo, cũng chưa có số ảnh hợp lệ riêng cho mỗi ứng viên.

Quyết định: giữ danh mục thực vật làm nguồn tìm kiếm; cách ly tên DOUBTFUL để đối chiếu; loại các giới ngoài thực vật khỏi phạm vi dự án. Giữ tên gốc và nguồn phân loại trước khi chuẩn hóa. Ảnh GBIF cần kiểm tra giấy phép từng ảnh, không lấy giấy phép metadata thay cho giấy phép ảnh.

### 2.2. TDTU VQA

Đã tải đủ ba tệp metadata và tính lại:

| Tập nguồn | Cặp hỏi–đáp | Đường dẫn ảnh khác nhau |
|---|---:|---:|
| Train | 23.271 | 3.032 |
| Validation | 2.954 | 379 |
| Test | 2.926 | 379 |
| Tổng | **29.151** | **3.790** |

Không có đường dẫn ảnh trùng giữa ba tập. Kết quả này chỉ nói về tên/đường dẫn; không chứng minh ảnh pixel, cá thể hay phiên chụp độc lập.

Truy hồi bằng tên nhận diện chính xác tìm được **69 ứng viên ảnh cho 19/20 loài**. Chưa tìm được tên chính xác “Ổi” trong lượt lọc này. Không dùng chứa chuỗi để gán loài: 56 ảnh có tên gần giống bị loại khỏi bước tự gán, chẳng hạn “rau má lông”, “bông ổi”, “gừng gió”, “nghệ trắng”. Không kết luận các ảnh đó sai hoặc vô giá trị; chỉ chưa thuộc đúng loài mục tiêu.

Đã chọn một ảnh đầu tiên theo thứ tự tên file cho mỗi loài có ứng viên, thử tải 19 và tải được 18. Một ảnh đậu biếc gặp lỗi tải. Đây là mẫu có chủ đích, **không phải mẫu ngẫu nhiên để ước lượng tỷ lệ lỗi toàn bộ dataset**.

### 2.3. Phát hiện quan trọng từ 18 ảnh đã mở

Có **8 ảnh nghi không phù hợp hình thái của nhãn nguồn**. Một cặp ảnh có SHA-256 giống hệt nhau nhưng mang hai nhãn khác nhau. Các quyết định dưới đây là sàng lọc bằng thị giác có hỗ trợ AI, chưa thay thế định danh thực vật của chuyên gia.

| File ảnh trong TDTU | Nhãn metadata | Quan sát và quyết định |
|---|---|---|
| `P000002956.jpg` | Diếp cá | Cành có lá nhỏ và hoa vàng; không phù hợp mô tả diếp cá. Cách ly. |
| `P000001990.jpg` | Lá lốt | Hoa dạng đầu với các hoa lưỡi trắng; không phù hợp cụm hoa dạng bông của lá lốt. Cách ly. |
| `P000001862.jpg` | Lô hội | Lá hình quạt và cấu trúc quả/hạt treo; không phù hợp lô hội. Cách ly. |
| `P000002062.jpg` | Cỏ nhọ nồi | Hoa lớn và đài đỏ; không phù hợp cụm hoa nhỏ của cỏ nhọ nồi. Cách ly. |
| `P000002366.jpg` | Ích mẫu | Hoa lớn, cánh dài dạng sao; không phù hợp nhãn. Cách ly. |
| `P000002789.jpg` | Gừng | Cành có cấu trúc quả đỏ; không phù hợp dạng cây gừng. Cách ly. |
| `P000001674.jpg` | Nghệ vàng | Hình giống đầu hoa atisô, không phù hợp cây nghệ. Cách ly, chưa đổi sang loài khác. |
| `P000003654.jpg` | Dâu tằm | Hoa sao trắng, nhị vàng; không phù hợp dâu tằm. Cách ly. |
| `P000000839.jpg` | Bụp giấm | Hình thái sơ bộ phù hợp nhưng trùng hoàn toàn byte với `P000002062.jpg`. Cách ly cả nhóm nhãn mâu thuẫn. |

SHA-256 của cặp nhãn cỏ nhọ nồi/bụp giấm: `3aac01cdc1e9188d6b45dd5a49f7c5865533898eabbf47d9abee5c63697fa14a`.

Trong 18 ảnh mẫu: **7 ảnh có thể tiếp tục rà soát**, **9 ảnh cách ly**, **2 ảnh dành cho tư liệu/nhánh ảnh mẫu tách rời**. Bảy ảnh sơ bộ phù hợp không đồng nghĩa đã xác nhận loài hoặc quyền sử dụng. Có watermark trên nhiều ảnh; cần kiểm tra nguồn ảnh gốc và nguy cơ mô hình học logo.

Toàn bộ 69 ứng viên vẫn có `training_eligible=false`. Còn 51 ảnh chưa được mở trong lượt này. Quyết định theo từng file lưu ở `results/candidate_images_reviewed.json` và lý do chi tiết ở `results/visual_review.json`.

**Kết luận về nguồn:** chưa dùng TDTU VQA làm bộ huấn luyện chính hoặc đưa nguyên văn câu trả lời lên website. Cần truy nguyên ảnh–nhãn và rà soát nội dung trước. Không tự sửa các nhãn sai bằng phỏng đoán của AI.

## 3. Loài nên thu thập

Số ảnh TDTU trong bảng là số **ứng viên khớp tên**, gồm cả ảnh đang nghi sai nhãn; không phải số ảnh sạch. Metadata Viet Medi Species có dòng tương ứng cho cả 20 loài, nhưng số ảnh hợp lệ từng loài còn chưa xác minh.

| Mã | Tên dùng hiển thị | Tên khoa học mục tiêu | Ưu tiên | Ứng viên tên TDTU |
|---|---|---|---:|---:|
| VN001 | Rau má | Centella asiatica | 1 | 3 |
| VN002 | Diếp cá | Houttuynia cordata | 1 | 3 |
| VN003 | Tía tô | Perilla frutescens | 1 | 3 |
| VN004 | Húng chanh | Coleus amboinicus | 1 | 3 |
| VN005 | Lá lốt | Piper sarmentosum | 1 | 3 |
| VN006 | Trầu không | Piper betle | 1 | 3 |
| VN007 | Lô hội | Aloe vera | 1 | 3 |
| VN008 | Thuốc bỏng | Kalanchoe pinnata | 1 | 3 |
| VN009 | Cỏ nhọ nồi | Eclipta prostrata | 1 | 3 |
| VN010 | Xuyên tâm liên | Andrographis paniculata | 1 | 3 |
| VN011 | Ích mẫu | Leonurus japonicus | 1 | 3 |
| VN012 | Râu mèo | Orthosiphon aristatus | 1 | 5 |
| VN013 | Gừng | Zingiber officinale | 2 | 5 |
| VN014 | Nghệ vàng | Curcuma longa | 2 | 6 |
| VN015 | Sả chanh | Cymbopogon citratus | 2 | 5 |
| VN016 | Ổi | Psidium guajava | 2 | 0 |
| VN017 | Dâu tằm | Morus alba | 2 | 3 |
| VN018 | Bụp giấm | Hibiscus sabdariffa | 2 | 6 |
| VN019 | Đậu biếc | Clitoria ternatea | 2 | 3 |
| VN020 | Chùm ngây | Moringa oleifera | 2 | 3 |

Ưu tiên 1 là nhóm cây phù hợp thí điểm lá–thân–toàn cây, có hồ sơ đối chiếu và tạo được các bài so sánh hình thái. Đây là lựa chọn phạm vi của dự án, chưa phải bảng xếp hạng mức phổ biến trên toàn Việt Nam. Nhóm lá lốt/trầu không/diếp cá là nhóm thử nhầm lẫn dự kiến theo hình dạng lá; phải xác nhận nhầm lẫn thực tế sau huấn luyện. Không gọi đây là cây thay thế nhau hoặc cùng công dụng.

Húng chanh: giữ Plectranthus amboinicus làm tên đồng nghĩa của Coleus amboinicus. Lá lốt: giữ tên Piper lolot cùng nguồn tham chiếu khi ánh xạ sang Piper sarmentosum. Với râu mèo, những tên Orthosiphon stamineus/spiralis cần rà soát trước khi gộp mẫu. “Thuốc bỏng”, “sống đời”, “trường sinh” cũng không đủ để tự xác nhận một ảnh là Kalanchoe pinnata.

Ngải cứu, bạc hà, diệp hạ châu, mã đề và cà gai leo để nhóm chờ. Mục đích là xử lý tên loài và ảnh cây dễ nhầm trước khi mở thêm lớp. Không xóa nhu cầu học về các cây này; website có thể giới thiệu bài đã thẩm định trước khi mô hình nhận diện được chúng.

## 4. Ảnh và nhãn phải giữ

Giữ ảnh tươi rõ nét, có nền đa dạng thật; giữ cả biến thiên lá non/già, xanh/tía và các giai đoạn có hoa/quả. Mỗi lần quan sát ưu tiên mặt trên lá, mặt dưới lá, thân–đốt/cách mọc lá và toàn cây. Hoa/quả là phần bổ sung; không bắt buộc đào rễ để nhận diện.

| Nhãn | Cách ghi |
|---|---|
| Loài | Mã ổn định VN001…VN020; tên nguồn; tên khoa học mục tiêu; trạng thái xác minh |
| Bộ phận nhìn thấy | Lá, thân, vỏ, hoa, quả, hạt, rễ, thân rễ; có thể nhiều nhãn |
| Góc chụp | Mặt trên/mặt dưới lá, thân–đốt, toàn cây, cận hoa… |
| Hình thái | Hình phiến, mép, cách mọc lá, màu từng mặt và thân; chỉ ghi khi nhìn thấy |
| Giai đoạn | Giai đoạn sinh dưỡng/nụ/hoa/quả được quan sát; cho phép thiếu |
| Tuổi | Chỉ có khi có bằng chứng gieo/trồng; còn lại để null |
| Nhóm | Cá thể/khóm/chậu, lần quan sát, phiên chụp và nhóm ảnh trùng |
| Nguồn/quyền | URL, bản ghi, tác giả, giấy phép, ghi công, quyền cho nghiên cứu và website |

Không dùng tên Việt làm khóa duy nhất. Không ghép lá của cây A, thân của cây B và hoa của cây C thành một quan sát của “cùng cây”. Không điền toàn bộ hình thái điển hình của một loài vào mỗi ảnh khi ảnh không thể hiện chúng. Thân rễ của gừng/nghệ phải phân biệt với rễ. Toàn cây là góc chụp.

Mô tả hình thái giúp con người đối chiếu và có thể dùng trong thí nghiệm đa phương thức sau này. Nếu mô tả chứa tên cây hoặc được chép từ hồ sơ loài theo nhãn, đưa nó vào mô hình nhận diện sẽ gây rò rỉ đáp án. Giai đoạn hiện tại ưu tiên nhãn nhìn thấy được, chưa huấn luyện bằng văn bản chứa tên loài.

## 5. Điều kiện chốt bộ dữ liệu để huấn luyện

Mục tiêu thí điểm: 30–50 nhóm cá thể/khóm độc lập mỗi loài, khoảng bốn góc/nhóm. Với 12 loài, kế hoạch khoảng 1.440–2.400 ảnh. Đây là mục tiêu thu thập đề xuất, không phải lượng ảnh hiện có hay bảo đảm chất lượng mô hình. Thu nhiều ảnh cùng cây không thay cho nhiều cá thể.

Chia theo cây/khóm, không theo ảnh ngẫu nhiên. Tạm thiết kế 80% nhóm phát triển, 20% nhóm kiểm tra, ba fold theo nhóm trong tập phát triển; chốt trước khi tối ưu. Ảnh công khai thiếu mã cá thể không thể tự chứng minh khả năng nhận diện cây mới. Cần bộ kiểm tra tự chụp ở Việt Nam hoặc nguồn độc lập có kiểm định.

Thí nghiệm so sánh: SVM lá cơ sở; biểu diễn mới chỉ dùng lá; nhiều ảnh lá; nhiều bộ phận cùng số ảnh; kết hợp đều; tối ưu trọng số kết hợp. Mọi mô hình dùng cùng dữ liệu và tập kiểm tra của nghiên cứu mới. Báo Macro-F1, recall từng loài, ảnh nhầm, khoảng tin cậy và thời gian xử lý; kiểm tra thiếu bộ phận và mẫu ngoài danh sách.

## 6. Kết quả bàn giao và bước tiếp theo

Đã có danh sách loài máy đọc được, quy tắc giữ/loại/cách ly, lược đồ nhãn, danh sách 69 ứng viên, kết quả sàng lọc 18 ảnh và chương trình kiểm kê lại metadata. Chưa có ảnh được xác nhận đủ mọi điều kiện huấn luyện trong đợt này.

Bước tiếp theo là kiểm kê ảnh có nguồn gốc rõ cho 12 loài ưu tiên, xác minh nhãn và quyền từng ảnh, thống kê số quan sát ghép thật, rồi bổ sung ảnh cây ở Việt Nam cho chỗ thiếu. Chỉ bắt đầu huấn luyện khi manifest đã qua các bước này. Danh mục website có thể rộng hơn danh mục mô hình, nhưng nội dung và ảnh đăng phải được rà soát riêng.

Tài liệu nguồn, URL gốc, giới hạn quyền và căn cứ phân loại nằm trong `SOURCES.md`. Quy trình chi tiết nằm trong `SELECTION_PROTOCOL.md`.

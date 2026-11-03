# Nguồn và cách kiểm tra — 29/10/2026

## Dữ liệu đã đọc bằng chương trình

1. VietMediSpecies, nhánh `feature/update` của tác giả: [metadata loài](https://github.com/trientran/VietMediSpecies/blob/feature/update/merged_species_with_gbif_metadata.csv), [thống kê ảnh](https://github.com/trientran/VietMediSpecies/blob/feature/update/image_statistics.json). Metadata ghi 4.799 dòng; tệp thống kê ghi 3.570 loài có ảnh, trong đó 3.450 thực vật. Đây là hai khái niệm khác nhau. Chưa xác minh toàn bộ archive và chưa có thống kê ảnh từng loài. Tác giả công bố metadata CC BY 4.0; ảnh giữ giấy phép gốc riêng.
2. [Trang phát hành Viet Medi Species](https://www.scidb.cn/en/detail?dataSetId=d2e66ca3d73540739a39789d9b1cf989), DOI 10.57760/sciencedb.013q9. Phân biệt số loài trong danh mục với số loài thực sự có ảnh; không dùng thống kê giới thiệu làm số ảnh huấn luyện đã kiểm định.
3. [TDTU VQA Dataset Herb](https://huggingface.co/datasets/azan100an/tdtu_vqa_dataset_herb), [README gốc](https://huggingface.co/datasets/azan100an/tdtu_vqa_dataset_herb/raw/main/README.md). Đã đọc đủ ba tệp train/val/test metadata; số QA là 29.151, số đường dẫn ảnh khác nhau là 3.790. Giấy phép công bố CC BY-NC 4.0. Dataset card tự ghi dữ liệu chưa được xác minh độc lập bởi dược sĩ/nhà thực vật. Kiểm tra ảnh mẫu chỉ xác định chất lượng và dạng ảnh, không chứng nhận danh tính thực vật hoặc quyền của tác giả ảnh gốc.

SHA-256 các tệp đã tải lưu tại `results/source_hashes.json`; URL và trạng thái tải metadata tại `sources/retrieval_log.json` trong bản làm việc. Bộ bàn giao chỉ chứa kết quả dẫn xuất và URL, không đóng gói lại toàn bộ dữ liệu/ảnh của bên thứ ba.

## Nguồn đã xem nhưng chưa có kiểm kê ảnh đầy đủ

4. [VNPlant-200 — bài gốc](https://link.springer.com/chapter/10.1007/978-3-030-49264-9_37), DOI 10.1007/978-3-030-49264-9_37; [repo phát hành](https://github.com/kencoca/VietNam-Medicinal-Plant). Bài công bố 20.000 ảnh/200 loài. Repo hiện đọc được README và liên kết Drive; công cụ tra cứu trả lỗi 404 khi mở liên kết Drive. Điều này chưa chứng minh dữ liệu đã mất hoặc mọi người đều không truy cập được. Chưa nhận được danh sách nhãn/ảnh để kiểm kê và chưa xác minh giấy phép tái sử dụng, nên chưa chọn làm dữ liệu đầu vào mặc định.
5. [TCMP-300 — bài gốc](https://www.nature.com/articles/s41597-025-05522-7), DOI 10.1038/s41597-025-05522-7. Chỉ xem là nguồn bổ sung; cần kiểm tra loài trùng, nhãn bộ phận, ảnh trùng liên nguồn và giấy phép ảnh gốc trước khi nhập.

## Định danh và thiết kế nhãn

6. [Vườn thực vật — Khoa Dược, Đại học Tôn Đức Thắng](https://pharmacy.tdtu.edu.vn/duoc-lieu/botanical-garden). Liên kết hồ sơ từng loài nằm trong `species_policy.json`; bổ sung [Ổi — Đại học Y Dược TP.HCM](https://mplant.ump.edu.vn/index.php/oi-psidium-guajava-myrtaceae/). Dùng để đối chiếu tên và đặc điểm; không mặc định cho phép sao chép ảnh hoặc toàn văn.
7. [Coleus amboinicus — POWO/Kew](https://powo.science.kew.org/taxon/445902-1): tên được chấp nhận và Plectranthus amboinicus là đồng nghĩa; có ghi du nhập tại Việt Nam.
8. [Piper lolot — POWO/Kew](https://powo.science.kew.org/taxon/urn:lsid:ipni.org:names:681996-1): đồng nghĩa của Piper sarmentosum. Giữ lại tên nguồn, chỉ hợp nhất sau rà soát mẫu.
9. [Orthosiphon aristatus — POWO/Kew](https://powo.science.kew.org/taxon/453446-1), [mô tả phân loại](https://powo.science.kew.org/taxon/urn%3Alsid%3Aipni.org%3Anames%3A77169348-1/general-information): tên Orthosiphon spiralis có lịch sử áp dụng và vấn đề danh pháp; chưa tự động gộp mọi mẫu mang tên này.
10. [Artemisia indica — POWO/Kew](https://powo.science.kew.org/taxon/179626-1) và [Ngải cứu — Đại học Y Dược TP.HCM](https://mplant.ump.edu.vn/index.php/ngai-cuu-artemisia-vulgaris-asteraceae/). Không mặc định Artemisia indica và A. vulgaris là cùng loài chỉ vì tên Việt tương tự.
11. [Mã đề — Khoa Dược TDTU](https://pharmacy.tdtu.edu.vn/duoc-lieu/ma-de): hồ sơ đề cập Plantago major và P. asiatica; giá trị dùng làm dược liệu không làm hai loài trở thành một nhãn nhận diện.
12. [LifeCLEF 2014 Plant Task](https://www.imageclef.org/2014/lifeclef/plant): đơn vị quan sát gồm nhiều ảnh của cùng cây trong cùng sự kiện. Dùng làm căn cứ thiết kế observation_id; observation_id không tự chứng minh các phiên khác nhau thuộc các cá thể khác nhau.
13. [Automatic fused multimodal deep learning for plant identification](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2025.1616020/full), DOI 10.3389/fpls.2025.1616020: tham khảo kết hợp bộ phận và thiếu bộ phận. Hiệu quả trên dữ liệu khác không phải dự báo điểm cho dự án này.
14. [GBIF Terms of Use](https://www.gbif.org/terms): giấy phép và yêu cầu ghi công cần theo nguồn; không coi việc tìm thấy ảnh công khai là đủ quyền đăng lại.

## Phạm vi của kết luận

Danh sách 20 loài là ưu tiên nghiên cứu; chưa phải 20 lớp đã có bộ ảnh sạch. Các con số kiểm kê được tính lại bằng `audit_metadata.py`. Chỉ sử dụng metadata để gợi ý ứng viên; trước khi đào tạo phải kiểm tra ảnh, nhãn, nguồn ảnh, nhóm trùng và đơn vị cá thể. Không có kết quả huấn luyện hoặc độ chính xác mới trong đợt này.

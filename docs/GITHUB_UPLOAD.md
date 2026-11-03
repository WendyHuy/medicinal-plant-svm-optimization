# Đưa bản v0.3 lên GitHub

Bản này được chuẩn bị để Huỳnh Gia Huy tự đăng lên tài khoản của mình. Chưa tạo repo hoặc publish qua phiên làm việc này.

## Giữ lịch sử commit bằng Git

Giải nén gói bàn giao. Thư mục `medicinal-leaf-svm` chứa mã và mô hình; tệp `medicinal_leaf_v03_history.bundle` chứa toàn bộ lịch sử. Cài Git và mở PowerShell ở thư mục có bundle, chạy:

```powershell
git clone medicinal_leaf_v03_history.bundle medicinal-leaf-git
cd medicinal-leaf-git
git log --oneline -10
```

Trên GitHub tạo repository trống, ví dụ `medicinal-plant-svm-optimization`, không thêm README/license/gitignore lúc tạo vì dự án đã có. Sao chép HTTPS URL repo của bạn, rồi chạy:

```powershell
git remote remove origin
git remote add origin https://github.com/TEN_TAI_KHOAN/TEN_REPO.git
git push -u origin main
```

Thay hai tên bằng tài khoản và repo thật. Git sẽ hướng dẫn đăng nhập. Không dán token vào mã nguồn hoặc báo cáo. Có thể tạo tag sau khi kiểm tra:

```powershell
git tag v0.3.0
git push origin v0.3.0
```

Mở tab Actions để kiểm tra workflow. Bản bàn giao đã kiểm tra cục bộ; không ghi rằng GitHub CI đã đạt khi chưa có run trên repo của bạn.

## Tải bằng giao diện web

Có thể tải các tệp bên trong `medicinal-leaf-svm` lên repo bằng Add file / Upload files. Cách này không bảo toàn lịch sử commit trong bundle. Không tải cả ZIP như một tệp duy nhất để thay cho mã nguồn.

Không tải `.venv`, raw dataset, archive ảnh, file tải dở hoặc cache. `.gitignore` đã loại các tệp này. Các trọng số trong `models/` nhỏ hơn giới hạn thông thường của GitHub và được đưa vào repo để chạy dự đoán ngay. Ảnh ví dụ có ghi công ở `examples/ATTRIBUTION.json`.

## Sau khi đăng

Kiểm tra README, báo cáo và notebook hiển thị. Dán URL repo thật vào nơi nộp bài. Lịch sử commit phản ánh đúng ngày làm việc; không đổi ngày để mô phỏng năm tuần. Phần mở rộng 12 loài Việt Nam vẫn là nghiên cứu dữ liệu, không đổi tên repo/README để tuyên bố đã nhận diện 12 loài.

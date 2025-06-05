
## Face Attendance System

## Giới thiệu
**Face Attendance System** là một dự án được xây dựng bằng Python, nhằm cung cấp giải pháp chấm công và điểm danh tự động thông qua nhận diện khuôn mặt. Hệ thống này được thiết kế để nâng cao hiệu quả và độ chính xác trong việc quản lý thời gian và danh sách điểm danh của các tổ chức.

## Tính năng chính
- Nhận diện khuôn mặt nhanh chóng và chính xác.
- Ghi lại thời gian điểm danh tự động.
- Tích hợp với cơ sở dữ liệu để lưu trữ và quản lý dữ liệu điểm danh.
- Giao diện thân thiện và dễ sử dụng.
- Hỗ trợ nhiều người dùng cùng lúc.

## Ngôn ngữ và Công nghệ
- **Python**: 100%

## Cách cài đặt

1. **Yêu cầu hệ thống**:
   - Python 3.x
   - Webcam hoặc camera phù hợp.
   - Thư viện cần thiết (được liệt kê trong `requirements.txt`).

2. **Hướng dẫn cài đặt**:
   ```bash
   # Clone repository về máy
   git clone https://github.com/Techsolutions2024/face-atendance.git

   # Di chuyển vào thư mục dự án
   cd face-atendance

   # Cài đặt các thư viện cần thiết
   pip install -r requirements.txt
   ```

3. **Chạy dự án**:
   ```bash
   uvicorn api.identify:app --reload
   ```

## Hướng dẫn sử dụng

1. Cài đặt hệ thống và đảm bảo kết nối camera hoạt động.
2. Chạy server FastAPI bằng lệnh ở trên.
3. Mở `frontend/index.html` trên trình duyệt để chụp ảnh và gửi embedding.
4. Hệ thống sẽ trả về kết quả nhận diện và ghi nhận chấm công.

## Cấu trúc thư mục

```plaintext
face-atendance/
│
├── api/                 # FastAPI serverless functions
│   └── identify.py      # API nhận diện khuôn mặt
├── frontend/            # Giao diện web đơn giản
│   └── index.html
├── requirements.txt     # Thư viện Python cần thiết
└── README.md            # Tệp hướng dẫn (bạn đang đọc)
```

## Deploy lên Vercel
1. Tạo GitHub repository và push mã nguồn này.
2. Vào dashboard Vercel, chọn **New Project** và kết nối tới repo.
3. Thiết lập thư mục root ở repo và đảm bảo Vercel nhận diện thư mục `api/` làm Serverless Functions.
4. Mỗi lần push lên GitHub, Vercel sẽ tự động build và cung cấp URL cho hệ thống.

## Đóng góp
Chúng tôi khuyến khích các đóng góp từ cộng đồng! Nếu bạn muốn đóng góp, hãy thực hiện các bước sau:
1. Fork repository này.
2. Tạo một nhánh mới: `git checkout -b feature/your-feature-name`.
3. Commit thay đổi của bạn: `git commit -m 'Add new feature'`.
4. Push lên nhánh của bạn: `git push origin feature/your-feature-name`.
5. Tạo một pull request trên GitHub.

## Giấy phép
Dự án này được phát hành dưới giấy phép [MIT License](LICENSE). Vui lòng đọc tệp LICENSE để biết thêm chi tiết.

## Liên hệ
Nếu bạn có bất kỳ câu hỏi hoặc đề xuất nào, vui lòng liên hệ:
- **Email**: support@techsolutions2024.com
- **GitHub**: [Techsolutions2024](https://github.com/Techsolutions2024)

---

Cảm ơn bạn đã sử dụng **Face Attendance System**!

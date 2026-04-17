# Day 12 Lab - Mission Answers

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found
1. **Hardcode API key và thông tin nhạy cảm**: Việc để OPENAI_API_KEY và DATABASE_URL trực tiếp trong mã nguồn khiến bí mật của bạn dễ dàng bị lộ khi chia sẻ code hoặc đẩy lên GitHub.
2. **Cố định Host và Port**: Sử dụng host="localhost" và port=8000 khiến ứng dụng bị cô lập, không thể kết nối được với các dịch vụ bên ngoài hoặc chạy trên các nền tảng đám mây (Cloud).
3. **Sử dụng lệnh print thay vì Logging**: Cách này không chỉ thiếu chuyên nghiệp mà còn gây rủi ro bảo mật cực lớn khi vô tình in cả các mã khóa bí mật ra màn hình điều khiển hoặc file log.
4. **Thiếu endpoint Health Check**: Không có cơ chế /health để hệ thống giám sát biết được agent đang "sống" hay "chết", dẫn đến việc không thể tự động khởi động lại ứng dụng khi xảy ra lỗi.
5. **Kích hoạt Debug/Reload trong Production**: Việc để reload=True khi triển khai thực tế sẽ làm tiêu tốn tài nguyên hệ thống và làm giảm tính ổn định của Agent.

### Exercise 1.3: Comparison table

| Feature | Basic | Advanced | Why Important? |
|---------|-------|----------|---------------------|
| Config | Hardcode | Env vars | Tránh lộ bí mật (API key) và dễ dàng thay đổi cấu hình mà không cần sửa mã nguồn. |
| Health check | Không có | Có các endpoint /health, /ready | Giúp hệ thống tự động (Docker/K8s) theo dõi trạng thái để khởi động lại nếu app bị treo. |
| Logging | print() | Structured JSON Logging | Giúp truy vết lỗi dễ dàng hơn và tránh việc vô tình in các thông tin nhạy cảm ra log. |
| Shutdown | Đột ngột | Graceful Shutdown | Đảm bảo các yêu cầu đang xử lý được hoàn tất và đóng các kết nối (DB) an toàn trước khi tắt. |

---

## Part 2: Docker

### Exercise 2.1: Dockerfile questions
1. **Base image**: Base image được sử dụng là `python:3.11`. Đây là bản phân phối Python đầy đủ, có kích thước lớn nhưng ổn định.
2. **Working directory**: Working directory bên trong container được thiết lập là `/app`.
3. **Tại sao COPY requirements.txt trước?**: Để tận dụng **Docker layer cache**. Nếu file requirements không đổi, Docker sẽ bỏ qua bước `pip install` giúp build nhanh hơn nhiều.
4. **CMD vs ENTRYPOINT khác nhau thế nào?**:
   - `CMD`: Thiết lập lệnh mặc định, có thể bị ghi đè khi chạy container.
   - `ENTRYPOINT`: Thiết lập lệnh cố định, các tham số truyền thêm sẽ được nối tiếp vào lệnh này.

### Exercise 2.3: Image size comparison
- **Develop (Full Python)**: ~1.6 GB
- **Production (Multi-stage + Slim)**: ~230 MB
- **Difference**: Giảm được khoảng 85%, giúp deploy nhanh hơn và tiết kiệm lưu trữ.

---

## Part 3: Cloud Deployment

### Exercise 3.1: Railway deployment
- **URL**: [https://day12-production-17df.up.railway.app](https://day12-production-17df.up.railway.app)
- **Status**: Deployed successfully.

---

## Part 4: API Security

### Exercise 4.1-4.3: Test results
- **Authentication**: Thành công. Khi không có API Key trả về 401. Khi có key trả về 200.
- **Rate Limiting**: Đã cài đặt Sliding Window (10 req/min). Khi vượt quá trả về 429.
- **Security Headers**: Đã thêm `X-Content-Type-Options`, `X-Frame-Options` và ẩn header `Server`.

### Exercise 4.4: Cost guard implementation
- **Approach**: Sử dụng một biến `_daily_cost` để theo dõi chi phí giả lập dựa trên token. Token được tính bằng số từ * 2. Ngân sách mặc định là $10/ngày. Nếu vượt quá sẽ trả về 503.

---

## Part 5: Scaling & Reliability

### Exercise 5.1-5.5: Implementation notes
- **Stateless**: Đã cấu hình để có thể sử dụng Redis lưu trữ Rate Limit và Cost. Nếu không có Redis sẽ fallback về in-memory.
- **Graceful Shutdown**: Đã implement handler cho tín hiệu SIGTERM để app có thời gian dọn dẹp trước khi tắt.
- **Health/Ready**: Đã tách biệt `/health` (liveness) và `/ready` (readiness) để Load Balancer quản lý traffic tốt hơn.

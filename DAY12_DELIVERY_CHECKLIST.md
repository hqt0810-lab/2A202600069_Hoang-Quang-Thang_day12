#  Delivery Checklist — Day 12 Lab Submission

> **Student Name:** Hoàng Quang Thắng  
> **Student ID:** 2A202600069  
> **Date:** 17/04/2026

---

##  Submission Requirements

Submit a **GitHub repository** containing:

### 1. Mission Answers (40 points)

Create a file `MISSION_ANSWERS.md` with your answers to all exercises:

# Day 12 Lab - Mission Answers

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found
1. Hardcode API key và thông tin nhạy cảm: Việc để OPENAI_API_KEY và DATABASE_URL trực tiếp trong mã nguồn khiến bí mật của bạn dễ dàng bị lộ khi chia sẻ code hoặc đẩy lên GitHub.

2. Cố định Host và Port: Sử dụng host="localhost" và port=8000 khiến ứng dụng bị cô lập, không thể kết nối được với các dịch vụ bên ngoài hoặc chạy trên các nền tảng đám mây (Cloud).

3. Sử dụng lệnh print thay vì Logging: Cách này không chỉ thiếu chuyên nghiệp mà còn gây rủi ro bảo mật cực lớn khi vô tình in cả các mã khóa bí mật ra màn hình điều khiển hoặc file log.

4. Thiếu endpoint Health Check: Không có cơ chế /health để hệ thống giám sát biết được agent đang "sống" hay "chết", dẫn đến việc không thể tự động khởi động lại ứng dụng khi xảy ra lỗi.

5. Kích hoạt Debug/Reload trong Production: Việc để reload=True khi triển khai thực tế sẽ làm tiêu tốn tài nguyên hệ thống và làm giảm tính ổn định của Agent.

### Exercise 1.3: Comparison table


| Feature | Basic | Advanced | Why Important? |
|---------|-------|----------|---------------------|
| Config | Hardcode | Env vars | Tránh lộ bí mật (API key) và dễ dàng thay đổi cấu hình mà không cần sửa mã nguồn. |
| Health check | Không có | Có các endpoint /health, /ready | Giúp hệ thống tự động (Docker/K8s) theo dõi trạng thái để khởi động lại nếu app bị treo. |
| Logging | print() | Structured JSON Logging | Giúp truy vết lỗi dễ dàng hơn và tránh việc vô tình in các thông tin nhạy cảm ra log. |
| Shutdown | Đột ngột | Graceful Shutdown | Đảm bảo các yêu cầu đang xử lý được hoàn tất và đóng các kết nối (DB) an toàn trước khi tắt. |



## Part 2: Docker

### Exercise 2.1: Dockerfile questions
1. Base image: Base image được sử dụng là python:3.11. Đây là bản phân phối Python đầy đủ, có kích thước khoảng 1 GB
2. Working directory: Working directory (thư mục làm việc) bên trong container được thiết lập là /app. Mọi lệnh tiếp theo như COPY hay RUN sẽ được thực hiện tại thư mục này.
3. Tại sao COPY requirements.txt trước? Việc copy requirements.txt trước khi copy toàn bộ mã nguồn là để tận dụng Docker layer cache (bộ nhớ đệm tầng).
 - Tối ưu hóa thời gian build: Docker sẽ kiểm tra xem tệp requirements.txt có thay đổi không. Nếu không thay đổi, nó sẽ bỏ qua bước cài đặt thư viện (pip install) vốn tốn rất nhiều thời gian và sử dụng lại kết quả từ lần build trước.
 - Nếu copy toàn bộ code trước, mỗi khi chỉ cần sửa một dòng comment trong app.py, Docker sẽ buộc phải chạy lại lệnh pip install từ đầu vì tầng (layer) chứa code đã bị thay đổi.
4. CMD vs ENTRYPOINT khác nhau thế nào? 
 - CMD (Command): Thiết lập lệnh mặc định cho container. Lệnh này có thể bị ghi đè dễ dàng khi bạn chạy lệnh docker run. Ví dụ: docker run agent-develop bash sẽ chạy bash thay vì python app.py.\
- ENTRYPOINT: Thiết lập lệnh "cứng" cho container. Nó thường được dùng cho các container đóng vai trò như một công cụ thực thi chuyên biệt. Các tham số bạn truyền vào khi docker run sẽ được nối thêm vào sau lệnh của ENTRYPOINT chứ không ghi đè hoàn toàn như CMD.

### Exercise 2.3: Image size comparison
- Develop: 1660 MB
- Production: 236 MB
- Difference: ~85.8%

## Part 3: Cloud Deployment

### Exercise 3.1: Railway deployment
- URL: https://day12-production-ai-agent.up.railway.app/
- Screenshot: [Link to screenshot in repo]

### Exercise 3.2: Render deployment
- Platform: Render (Blueprint via render.yaml)
- Runtime: Python 3.11
- Region: Singapore
- Health Check Path: /health
- Auto Deploy: Enabled (on git push)

## Part 4: API Security

### Exercise 4.1: API Key Authentication (Basic — Folder 04 Develop)
Triển khai xác thực bằng API Key thông qua header `X-API-Key`.

**Kết quả test thực tế:**

Test 1 — Không có API Key → 401 Unauthorized:
```
PS> Invoke-RestMethod -Uri "http://localhost:8000/ask?question=Hello" -Method Post
→ The remote server returned an error: (401) Unauthorized.
```

Test 2 — Key sai → 403 Forbidden:
```
PS> Invoke-RestMethod -Uri "http://localhost:8000/ask?question=Hello" -Method Post -Headers @{"X-API-Key"="wrong-key"}
→ The remote server returned an error: (403) Forbidden.
```

Test 3 — Key đúng → 200 OK:
```
PS> Invoke-RestMethod -Uri "http://localhost:8000/ask?question=Hello" -Method Post -Headers @{"X-API-Key"="my-secret-123"}
→ {"question": "Hello", "answer": "Tôi là AI agent được deploy lên cloud. Câu hỏi của bạn: Hello"}
```

### Exercise 4.2: JWT Authentication (Production — Folder 04 Production)
Triển khai xác thực bằng JWT Token. Sử dụng Flask để tương thích Python 3.14.

**Kết quả test thực tế:**

Test 4 — Lấy JWT Token:
```
PS> Invoke-RestMethod -Uri http://localhost:8000/auth/token -Method Post -ContentType "application/json" -Body '{"username": "student", "password": "demo123"}'
→ {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzdHVkZW50Iiwicm9sZSI6InVzZXIi....",
    "token_type": "bearer"
  }
```

Test 5 — Dùng JWT Token để hỏi Agent → 200 OK:
```
PS> Invoke-RestMethod -Uri http://localhost:8000/ask -Method Post -ContentType "application/json" -Body '{"question": "What is Docker?"}' -Headers @{"Authorization"="Bearer $tk"}
→ {
    "question": "What is Docker?",
    "answer": "Container là cách đóng gói app để chạy ở mọi nơi. Build once, run anywhere!",
    "usage": {"cost_usd": 0.000019, "remaining_requests": 9}
  }
```

Test 6 — Không có Token → 401 Unauthorized:
```
PS> Invoke-RestMethod -Uri http://localhost:8000/ask -Method Post -ContentType "application/json" -Body '{"question": "Hello"}'
→ The remote server returned an error: (401) Unauthorized.
```

### Exercise 4.3: Rate Limiting
Thuật toán Sliding Window Counter:
- User tier: 10 requests/phút
- Admin tier: 100 requests/phút
- Khi vượt quá → trả về 429 Too Many Requests kèm retry_after

### Exercise 4.4: Cost guard implementation
Cost Guard bảo vệ ngân sách LLM (kết quả thực tế từ Test 5):
- Mỗi request ghi nhận usage: cost_usd = $0.000019, remaining_requests = 9
- Per-user daily budget: $1.00/ngày
- Global daily budget: $10.00/ngày
- Cảnh báo khi dùng 80% budget, block khi vượt (402/503)

## Part 5: Scaling & Reliability

### Exercise 5.1: Health Check
**Kết quả test thực tế — Liveness Probe (GET /health):**
```
PS> Invoke-RestMethod -Uri http://localhost:8000/health
→ {
    "status": "ok",
    "uptime_seconds": 17.6,
    "version": "1.0.0",
    "environment": "development",
    "timestamp": "2026-04-17T15:28:28.615073+00:00",
    "checks": {
      "memory": {"status": "ok", "used_percent": 67.7}
    }
  }
```

**Kết quả test thực tế — Readiness Probe (GET /ready):**
```
PS> Invoke-RestMethod -Uri http://localhost:8000/ready
→ {"ready": true, "in_flight_requests": 1}
```

### Exercise 5.2: Graceful Shutdown
Triển khai bằng signal handler:
- Bắt tín hiệu SIGINT/SIGTERM từ platform
- Đánh dấu `_is_ready = False` để ngừng nhận request mới
- Đợi tối đa 10 giây cho các request đang xử lý hoàn thành
- Log thông tin shutdown chi tiết

### Exercise 5.3: Request Tracking
Middleware `before_request` / `after_request` theo dõi in-flight requests:
- Tăng `_in_flight_requests` khi nhận request mới
- Giảm `_in_flight_requests` khi response hoàn thành
- Kết quả: readiness probe hiển thị `"in_flight_requests": 1` (chính request kiểm tra)

### Exercise 5.4-5.5: Stateless Design
- Agent stateless: không lưu trạng thái giữa các request
- Rate limiter/cost guard dùng in-memory cho demo, production nên dùng Redis
- Tất cả cấu hình qua environment variables (PORT, ENVIRONMENT, AGENT_API_KEY)
```

---

### 2. Full Source Code - Lab 06 Complete (60 points)

Your final production-ready agent with all files:

```
your-repo/
├── app/
│   ├── main.py              # Main application
│   ├── config.py            # Configuration
│   ├── auth.py              # Authentication
│   ├── rate_limiter.py      # Rate limiting
│   └── cost_guard.py        # Cost protection
├── utils/
│   └── mock_llm.py          # Mock LLM (provided)
├── Dockerfile               # Multi-stage build
├── docker-compose.yml       # Full stack
├── requirements.txt         # Dependencies
├── .env.example             # Environment template
├── .dockerignore            # Docker ignore
├── railway.toml             # Railway config (or render.yaml)
└── README.md                # Setup instructions
```

**Requirements:**
-  All code runs without errors
-  Multi-stage Dockerfile (image < 500 MB)
-  API key authentication
-  Rate limiting (10 req/min)
-  Cost guard ($10/month)
-  Health + readiness checks
-  Graceful shutdown
-  Stateless design (Redis)
-  No hardcoded secrets

---

### 3. Service Domain Link

Create a file `DEPLOYMENT.md` with your deployed service information:

```markdown
# Deployment Information

## Public URL
https://day12-production-ai-agent.up.railway.app/

## Platform
Railway

## Test Commands

### Health Check
```bash
curl https://day12-production-ai-agent.up.railway.app/health
# Expected: {"status": "ok"}
```

### API Test (with authentication)
```bash
curl -X POST https://day12-production-ai-agent.up.railway.app/ask \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "question": "Hello"}'
```

## Environment Variables Set
- PORT
- ENVIRONMENT
- AGENT_API_KEY
- LOG_LEVEL

## Screenshots
- [Deployment dashboard](screenshots/dashboard.png)
- [Service running](screenshots/running.png)
- [Test results](screenshots/test.png)
```

##  Pre-Submission Checklist

- [x] Repository is public (or instructor has access)
- [x] `MISSION_ANSWERS.md` completed with all exercises
- [ ] `DEPLOYMENT.md` has working public URL
- [x] All source code in `app/` directory
- [x] `README.md` has clear setup instructions
- [x] No `.env` file committed (only `.env.example`)
- [x] No hardcoded secrets in code
- [ ] Public URL is accessible and working
- [ ] Screenshots included in `screenshots/` folder
- [x] Repository has clear commit history

---

##  Self-Test

Before submitting, verify your deployment:

```bash
# 1. Health check
curl https://day12-production-ai-agent.up.railway.app/health

# 2. Authentication required
curl https://day12-production-ai-agent.up.railway.app/ask
# Should return 401

# 3. With API key works
curl -H "X-API-Key: YOUR_KEY" https://day12-production-ai-agent.up.railway.app/ask \
  -X POST -d '{"user_id":"test","question":"Hello"}'
# Should return 200

# 4. Rate limiting
for i in {1..15}; do 
  curl -H "X-API-Key: YOUR_KEY" https://day12-production-ai-agent.up.railway.app/ask \
    -X POST -d '{"user_id":"test","question":"test"}'; 
done
# Should eventually return 429
```

---

##  Submission

**Submit your GitHub repository URL:**

```
https://github.com/hqt0810/2A202600069_Hoang-Quang-Thang_day12
```

**Deadline:** 17/4/2026

---

##  Quick Tips

1.  Test your public URL from a different device
2.  Make sure repository is public or instructor has access
3.  Include screenshots of working deployment
4.  Write clear commit messages
5.  Test all commands in DEPLOYMENT.md work
6.  No secrets in code or commit history

---

##  Need Help?

- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- Review [CODE_LAB.md](CODE_LAB.md)
- Ask in office hours
- Post in discussion forum

---

**Good luck! **

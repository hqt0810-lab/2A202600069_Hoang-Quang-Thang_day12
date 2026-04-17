# Deployment Information

## Public URL
https://day12-production-17df.up.railway.app

## Platform
Railway (hoặc Render)

## Test Commands

### 1. Health Check
```bash
curl https://day12-production-17df.up.railway.app/health
```
**Expected Output:** `{"status": "ok", ...}`

### 2. API Test (Requires Authentication)
Thay `YOUR_KEY` bằng giá trị `AGENT_API_KEY` bạn đã set.
```bash
curl -X POST https://day12-production-17df.up.railway.app/ask \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Docker?"}'
```

### 3. Rate Limit Test
Chạy lệnh này liên tục nhiều lần:
```bash
for i in {1..15}; do curl -H "X-API-Key: YOUR_KEY" https://day12-production-17df.up.railway.app/ask -X POST -d '{"question":"test"}'; done
```

## Environment Variables Set
| Variable | Value | Purpose |
|----------|-------|---------|
| `PORT` | 8000 | Port cho server |
| `AGENT_API_KEY` | (your secret key) | Bảo mật API |
| `DAILY_BUDGET_USD` | 10.0 | Giới hạn chi phí |
| `ENVIRONMENT` | production | Tắt docs, bật bảo mật |
| `REDIS_URL` | (optional) | Để chạy stateless |

## Screenshots
Vui lòng lưu các ảnh sau vào thư mục `screenshots/`:
1. `dashboard.png`: Dashboard của Railway/Render.
2. `running.png`: Kết quả gọi API `/ask` thành công.
3. `test.png`: Kết quả test rate limit (mã 429).

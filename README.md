# SOA_DEMO

Demo yêu cầu vắng mặt: React + TanStack Form/Zod gửi yêu cầu tới FastAPI, Gmail API gửi email HTML, Gmail Watch + Google Cloud Pub/Sub webhook đọc phản hồi của quản lý và cập nhật SQLite.

## Chạy local

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Tạo `.env` ở root từ `.env.docker.example`. Gmail OAuth cần credential JSON, Gmail API scope `gmail.modify`, Google Cloud Pub/Sub topic `gmail-absent-updates` và push subscription trỏ tới HTTPS public URL `/api/webhooks/gmail?token=PUBSUB_VERIFICATION_TOKEN`. Trên VPS, dùng Nginx reverse proxy cấp TLS và chạy `docker compose exec app python start_watch.py` sau khi cấu hình credential. Lệnh này đăng ký watch và lưu `historyId` ban đầu vào SQLite.

Quản lý phản hồi email bằng đúng cú pháp `APPROVE AR-1` hoặc `REJECT AR-1`. Backend xác nhận email đến từ đúng `manager_email`, đọc Gmail History API sau thông báo Pub/Sub, rồi frontend tự polling để hiển thị trạng thái mới. `mailto:` chỉ mở email soạn sẵn; nó không phải callback.

## Chạy trên VPS bằng Docker

Yêu cầu: Docker Compose plugin, domain đã trỏ DNS A/AAAA về VPS và có một reverse proxy HTTPS ở trước container. Container này chỉ mở HTTP port `80`; Pub/Sub cần gọi URL HTTPS của reverse proxy.

```bash
cp .env.docker.example .env
mkdir -p secrets
# Copy Google OAuth client JSON vào secrets/credentials.json
docker compose build
docker compose up -d
docker compose exec app python start_watch.py
```

Nginx trong image phục vụ static frontend và proxy `/api` tới Uvicorn nội bộ. Pub/Sub push URL dùng `https://<APP_DOMAIN>/api/webhooks/gmail?token=<PUBSUB_VERIFICATION_TOKEN>` qua Nginx reverse proxy HTTPS của VPS. Dữ liệu SQLite và Gmail token nằm trong Docker volume `app_data`; OAuth client nằm ở `secrets/` và chỉ được mount read-only vào app. Không commit `.env`, `secrets/` hoặc credential Google vào git.
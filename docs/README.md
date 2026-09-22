# Sequence Diagram - Email Workflow với Gmail + Pub/Sub

## Xem Diagram

### Cách 1: VS Code Extension (Khuyên dùng)
Cài đặt extension **PlantUML** (jebbs.plantuml) trong VS Code, sau đó mở file `sequence-diagram.puml` và nhấn `Alt+D` để xem preview.

### Cách 2: Online Editor
Copy nội dung file `sequence-diagram.puml` vào: https://www.plantuml.com/plantuml/uml/

### Cách 3: Command Line (nếu có cài PlantUML)
```bash
# Cài đặt (macOS)
brew install plantuml

# Cài đặt (Ubuntu/Debian)
sudo apt install plantuml

# Render sang PNG
plantuml sequence-diagram.puml

# Render sang SVG
plantuml -tsvg sequence-diagram.puml
```

## Mô tả Workflow

### 1. Khởi tạo Gmail Watch
- Backend gọi `start_watch()` để đăng ký Gmail watch với Pub/Sub topic
- Gmail API tạo subscription và trả về `historyId` và `expiration`

### 2. Gửi email tới người dùng
1. Người dùng yêu cầu gửi email (qua API call)
2. Backend gọi Gmail API gửi email HTML tới người dùng
3. Email chứa 2 link `mailto:` với command `APPROVE {id}` và `REJECT {id}`
4. Backend nhận `message_id` từ Gmail API

### 3. Người dùng phản hồi qua Gmail
1. Người dùng reply email với command (ví dụ: `APPROVE 123e4567-e89b-12d3-a456-426614174000`)
2. Gmail API push notification tới Pub/Sub topic
3. Pub/Sub gửi webhook tới `POST /api/webhooks/gmail` kèm OIDC token
4. Backend xác thực OIDC token (verify service account email)
5. Backend decode base64 data lấy `historyId`
6. Backend gọi `sync_history()` để lấy messages mới từ Gmail API
7. Với mỗi message: parse subject/body tìm command bằng regex
8. Nếu hợp lệ: xử lý logic nghiệp vụ (cập nhật trạng thái, lưu kết quả)
9. Cập nhật `last_history_id`
10. Trả về `204 No Content` cho Pub/Sub

## Các thành phần chính

| Component | Công nghệ | Vai trò |
|-----------|-----------|---------|
| Backend | FastAPI | REST API, business logic, webhook handler |
| Gmail API | Google APIs | Gửi/nhận email, watch changes |
| Pub/Sub | Google Cloud | Push notifications từ Gmail |

## Cấu hình cần thiết (Environment Variables)

```env
# Backend
GMAIL_TOKEN_JSON_BASE64=...          # OAuth token cho Gmail API
GMAIL_SENDER=sender@gmail.com        # Email gửi đi
PUBSUB_OIDC_TOPIC=projects/{project}/topics/{topic}
PUBSUB_OIDC_AUDIENCE={audience}      # OIDC audience cho verification
PUBSUB_SERVICE_ACCOUNT_EMAIL=...@gserviceaccount.com
SECRET_KEY=your-jwt-secret
```

## Sequence Diagram Elements

- **Actor**: Người dùng bên ngoài hệ thống
- **Participant**: Các service/component tích cực xử lý logic
- **activate/deactivate**: Thể hiện thời gian component đang xử lý
- **loop**: Xử lý lặp qua nhiều message
- **alt/else**: Điều kiện phân nhánh
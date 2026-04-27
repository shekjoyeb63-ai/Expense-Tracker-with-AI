# 💸 Expense Tracker AI

A production-grade **Flask REST API** for personal expense tracking, built with enterprise-level backend patterns. This is not a tutorial project — it implements the same architectural patterns used by real companies like Razorpay, Zepto, and Groww.

---

## ⚡ What Makes This Different

| Feature | Implementation |
|---------|---------------|
| Authentication | JWT + Redis-backed token blacklisting |
| Email Verification | OTP via Gmail SMTP, stored in Redis with 5-min TTL |
| Response Caching | Redis cache on all GET endpoints, auto-invalidated on writes |
| Async Tasks | Celery + Redis broker for non-blocking email delivery |
| AI Integration | Claude API for auto expense categorization + RAG chatbot |
| Receipt Scanner | Claude Vision API extracts merchant, amount, date from photos |
| Testing | Pytest suite, zero real emails sent during tests |
| Deployment | Dockerized with Docker Compose |

---

## 🧠 Architecture

```
Flask App (Blueprint architecture)
├── Redis       → Token blacklist + Response cache + OTP store + Celery broker
├── PostgreSQL  → Persistent expense + user data
├── Celery      → Async email tasks + Monthly summaries
└── Claude AI   → Auto categorization + Expense insights chatbot
```

---

## 📁 Project Structure

```
EXPENSE-AI/
├── app/
│   ├── models/
│   │   ├── tables.py        # SQLAlchemy models
│   │   └── operations.py    # DB logic
│   ├── routes/
│   │   ├── auth.py          # register, login, logout, OTP
│   │   └── expenses.py      # expense CRUD + AI routes
│   ├── services/
│   │   ├── redis_client.py  # Redis connection
│   │   ├── celery_worker.py # Celery factory
│   │   ├── tasks.py         # Async tasks
│   │   ├── email_service.py # OTP email logic
│   │   └── ai_client.py     # Claude API integration
│   └── __init__.py          # App factory
├── tests/
│   ├── conftest.py
│   └── test_file.py
├── celery_app.py            # Celery entry point
├── docker-compose.yml
├── Dockerfile
├── run.py
└── requirements.txt
```

---

## 🛠️ Tech Stack

| Tool | Purpose |
|------|---------|
| Flask | Web framework |
| SQLAlchemy | ORM |
| PostgreSQL | Production database |
| Redis | Caching + message broker + OTP store |
| Celery | Async task queue |
| Claude API | AI categorization + chatbot |
| Flask-JWT-Extended | Authentication |
| Flask-Bcrypt | Password hashing |
| Flask-Limiter | Rate limiting |
| Flasgger | Swagger UI |
| Pytest | Testing |
| Docker | Containerization |

---

## ⚙️ Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/shekjoyeb63-ai/Expense-Tracker-AI.git
cd Expense-Tracker-AI
```

### 2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
Create a `.env` file in root:
```
JWT_SECRET_KEY=your_secret_key
DATABASE_URL=sqlite:///Expense.db
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_URL=redis://localhost:6379/0
MAIL_EMAIL=your_gmail@gmail.com
MAIL_PASSWORD=your_16_char_app_password
ANTHROPIC_API_KEY=your_anthropic_key
```

### 5. Start Redis
```bash
docker run -d --name redis -p 6379:6379 redis
```

### 6. Start Celery worker
```bash
celery -A celery_app worker --loglevel=info --pool=solo
```

### 7. Run the server
```bash
python run.py
```

Server starts at `http://127.0.0.1:5000`

---

## 🔐 Authentication Flow

```
POST /register   →  account created + OTP sent to email (async via Celery)
POST /verify-otp →  account activated
POST /login      →  JWT token issued
POST /logout     →  token blacklisted in Redis (auto-expires in 1hr)
```

---

## 🤖 AI Features

### Auto Categorization
Add an expense without a category — Claude automatically detects it:
```json
POST /add
{
    "title": "Swiggy biryani order",
    "amount": 340,
    "date": "2026-04-27"
}
```
Response:
```json
{
    "category": "Food"
}
```

### Expense Insights Chatbot
Ask questions about your spending in natural language:
```json
POST /chat
{
    "message": "How much did I spend on food this month?"
}
```
Response:
```json
{
    "answer": "You spent ₹2,340 on Food this month across 7 transactions. Your biggest purchase was Swiggy biryani at ₹340."
}
```

### Receipt Scanner
Upload a receipt photo — expense created automatically:
```
POST /scan-receipt
Content-Type: multipart/form-data
receipt: <image file>
```

---

## 📮 API Endpoints

### Auth
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/register` | Register + send OTP | ❌ |
| POST | `/verify-otp` | Verify email OTP | ❌ |
| POST | `/login` | Login + get JWT token | ❌ |
| POST | `/logout` | Logout + blacklist token | ✅ |

### Expenses
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/view` | View expenses (paginated + cached) | ✅ |
| POST | `/add` | Add expense (AI auto-categorizes) | ✅ |
| DELETE | `/delete` | Delete expense | ✅ |
| POST | `/search` | Search by category | ✅ |
| GET | `/view_total` | Total amount (cached) | ✅ |
| POST | `/date_range` | Filter by date range | ✅ |

### AI
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/chat` | Natural language expense insights | ✅ |
| POST | `/scan-receipt` | Auto-create expense from receipt photo | ✅ |

---

## 🚦 Rate Limiting

| Endpoint | Limit |
|----------|-------|
| `/register` | 5 per minute |
| `/login` | 3 per minute |
| All others | 200/day, 50/hr |

---

## ⚡ Redis Usage

| Purpose | Key Pattern | TTL |
|---------|-------------|-----|
| Token blacklist | `blacklist:{jti}` | 1 hour |
| OTP store | `otp:{email}` | 5 minutes |
| Expense cache | `expenses:{user_id}:page:{n}` | 60 seconds |
| Total cache | `total:{user_id}` | 60 seconds |
| AI category cache | `category:{description}` | 30 days |

---

## 🧪 Running Tests

```bash
pytest -v
```

Test suite covers authentication, CRUD operations, input validation, token blacklisting, OTP flow, and caching. No real emails sent during tests — OTP is read directly from Redis.

---

## 🐳 Docker

```bash
docker-compose up --build
```

Starts Flask + PostgreSQL + Redis + Celery in one command.

---

## 📖 API Docs

Interactive Swagger UI available at:
```
http://127.0.0.1:5000/apidocs
```

---

## 👨‍💻 Author

**Sheak Md Joyeb**
Python Backend Developer | NIT Durgapur
[LinkedIn](https://linkedin.com/in/sheak-md-joyeb) | [GitHub](https://github.com/shekjoyeb63-ai)

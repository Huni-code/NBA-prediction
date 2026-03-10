# 🏀 NBA Win Predictor

## 폴더 구조
```
NBA_prediction/
├── backend/        ← Python FastAPI 서버
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── routers.py
│   ├── requirements.txt
│   ├── .env
│   ├── etl/
│   │   └── pipeline.py
│   └── model/
│       └── predictor.py
└── frontend/       ← React 앱
    ├── src/
    │   ├── App.jsx
    │   └── main.jsx
    ├── index.html
    ├── package.json
    ├── vite.config.js
    └── .env.local
```

---

## 실행 전 준비 (1회만)

### PostgreSQL DB 만들기
pgAdmin 또는 SQL Shell(psql) 열고 실행:
```sql
CREATE DATABASE nba_predictor;
CREATE USER nba_user WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE nba_predictor TO nba_user;
```

---

## 실행 방법

### VS Code 터미널 1 — 백엔드
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### VS Code 터미널 2 — 프론트엔드 (+ 버튼으로 새 터미널)
```bash
cd frontend
npm install
npm run dev
```

---

## 확인
- 백엔드: http://localhost:8000/docs
- 앱:     http://localhost:5173

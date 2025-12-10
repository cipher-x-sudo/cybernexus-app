# CyberNexus Quick Start Guide

Get up and running in **5 minutes**.

---

## 🚀 Option 1: Docker (Fastest)

```bash
git clone https://github.com/your-org/cybernexus.git
cd cybernexus
docker-compose up -d
```

**Access:**
- 🖥️ **Dashboard**: http://localhost:3000
- 📡 **API**: http://localhost:8000
- 📚 **API Docs**: http://localhost:8000/docs

---

## 🛠️ Option 2: Manual Setup

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## 🔐 Login

| Username | Password |
|----------|----------|
| `admin` | `admin123` |

---

## ✅ First Steps

1. **Login** → Navigate to http://localhost:3000
2. **Dashboard** → View global threat map & stats
3. **Graph** → Explore 3D entity relationships
4. **Credentials** → Check for leaked credentials
5. **Dark Web** → Monitor brand mentions
6. **Reports** → Generate executive summaries

---

## 🔗 Key Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /api/v1/auth/login` | Authenticate |
| `GET /api/v1/entities` | List entities |
| `GET /api/v1/graph` | Get threat graph |
| `GET /api/v1/threats` | List threats |
| `GET /api/v1/threats/top?n=10` | Top N threats |
| `POST /api/v1/reports/generate` | Generate report |

---

## 📊 Dashboard Widgets

| Widget | What it Shows |
|--------|--------------|
| **Global Map** | Real-time attacks worldwide |
| **Stats Cards** | Threats, critical, resolved, score |
| **Donut Chart** | Threats by category |
| **Line Chart** | Threat trend over time |
| **Activity Feed** | Latest security events |
| **Heatmap** | Attack patterns by hour/day |

---

## 🗺️ Navigation

```
┌─ Dashboard      → Main overview
├─ Graph          → 3D entity visualization
├─ Credentials    → Leaked credential monitoring
├─ Dark Web       → Dark web surveillance
├─ Map            → Geographic threat view
├─ Reports        → Generate documentation
├─ Settings       → Configuration
└─ Help           → Support & FAQ
```

---

## 🎮 Graph Controls

| Action | Control |
|--------|---------|
| Rotate | Click + Drag |
| Zoom | Scroll |
| Select | Click node |
| Details | Right-click |
| Focus | Double-click |

---

## 🚨 Alert Levels

| Level | Color | Action Required |
|-------|-------|-----------------|
| **Critical** | 🔴 | Immediate |
| **High** | 🟠 | Same day |
| **Medium** | 🟡 | This week |
| **Low** | 🔵 | When possible |
| **Info** | ⚪ | Awareness only |

---

## 📁 Project Structure

```
cybernexus/
├── backend/
│   ├── app/
│   │   ├── api/routes/      # REST endpoints
│   │   ├── collectors/      # Data collectors
│   │   ├── core/dsa/        # DSA implementations
│   │   └── services/        # Business logic
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js pages
│   │   └── components/      # React components
│   └── package.json
└── docs/                    # Documentation
```

---

## 📚 Learn More

- **Full Guide**: [GUIDE.md](GUIDE.md)
- **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **DSA Deep Dive**: [DSA.md](DSA.md)
- **API Reference**: [API.md](API.md)

---

## 🆘 Troubleshooting

### Backend won't start

```bash
# Check Python version (needs 3.11+)
python --version

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Frontend won't start

```bash
# Check Node version (needs 18+)
node --version

# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Can't connect to API

```bash
# Check if backend is running
curl http://localhost:8000/health

# Check CORS settings in backend/app/main.py
```

---

<p align="center">
<strong>Need more help? See the <a href="GUIDE.md">Complete User Guide</a></strong>
</p>




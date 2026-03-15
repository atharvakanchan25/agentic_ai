# Timetable AI — Multi-Agent Scheduling System

University timetable generation using a multi-agent AI pipeline with constraint programming.

## Architecture

```
User Request
     │
     ▼
AgentOrchestrator
     │
     ├── ValidationAgent      → validates input data & constraints
     ├── ResourceAllocationAgent → assigns rooms & faculty
     ├── OptimizationAgent    → OR-Tools CP-SAT solver
     ├── ConflictResolutionAgent → detects & resolves conflicts
     └── AnalyticsAgent       → metrics, insights, report
```

## Project Structure

```
timetable_ai_system/
├── src/
│   ├── agents/              # 5 AI agents + orchestrator + base
│   ├── api/                 # FastAPI routes + Pydantic schemas
│   ├── database/            # SQLAlchemy models + session
│   └── mcp/                 # MCP server + client (WebSocket)
├── frontend/                # React + Vite UI
│   └── src/
│       ├── pages/           # DataPage, TimetablePage, ChatPage
│       ├── components/      # EntityTable (reusable CRUD)
│       └── api/             # Axios client
├── scripts/
│   └── seed.py              # Sample data seeder
├── main.py                  # FastAPI entry point
├── config.py                # All configuration
└── requirements.txt
```

## Quick Start

### 1. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 2. Seed the database with sample data
```bash
python scripts/seed.py
```

### 3. Start the backend
```bash
python main.py
```
→ API running at http://localhost:8000  
→ API docs at http://localhost:8000/docs

### 4. Start the frontend (new terminal)
```bash
cd frontend
npm install
npm run dev
```
→ UI running at http://localhost:3000

## Usage

1. **Data tab** — Add departments, subjects, rooms, faculty, divisions
2. **Timetable tab** — Select departments → Generate Timetable → View grid, insights, agent log
3. **Chat tab** — Natural language interface: "generate timetable", "show rooms", etc.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/departments` | List departments |
| POST | `/api/departments` | Create department |
| GET | `/api/subjects` | List subjects |
| POST | `/api/subjects` | Create subject |
| GET | `/api/rooms` | List rooms |
| POST | `/api/rooms` | Create room |
| GET | `/api/faculty` | List faculty |
| POST | `/api/faculty` | Create faculty |
| GET | `/api/divisions` | List divisions |
| POST | `/api/divisions` | Create division |
| POST | `/api/timetable/generate` | Generate timetable |
| POST | `/api/chat` | Chat interface |
| GET | `/docs` | Swagger UI |

## Troubleshooting

**Port in use:**
```bash
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

**Dependency issues:**
```bash
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```

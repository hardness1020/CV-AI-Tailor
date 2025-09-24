# Development Environment Setup

This document outlines different development environment options for CV Tailor.

## Option 1: VS Code DevContainer (Recommended)

**Best for**: Consistent development environment with Claude Code integration

### Architecture
```
┌─────────────────────────────────────┐
│  VS Code DevContainer               │
│  ├── Claude Code + Development Tools│
│  ├── Python (uv) + Node.js         │
│  └── Database clients              │
├─────────────────────────────────────┤
│  Docker Compose Services:          │
│  ├── PostgreSQL + pgvector         │
│  └── Redis                         │
└─────────────────────────────────────┘
```

### Setup Steps
1. **Open in VS Code**: `Ctrl+Shift+P` → "Reopen in Container"
2. **Wait for setup**: DevContainer builds automatically with all dependencies
3. **Services start**: PostgreSQL and Redis start automatically
4. **Ready to code**: All tools available in integrated terminal

### Usage
```bash
# Inside devcontainer terminal:
cd backend
uv sync                              # Install dependencies
uv run python manage.py migrate     # Setup database
uv run python manage.py runserver   # Start backend

# In another terminal:
cd frontend
npm install                          # Install dependencies
npm run dev                         # Start frontend
```

## Option 2: Host Development + Docker Services

**Best for**: Maximum performance, direct access to host tools

### Architecture
```
┌─────────────────────────────────────┐
│  Host System                       │
│  ├── Claude Code (native)          │
│  ├── Python (uv) + Node.js        │
│  └── VS Code + Extensions         │
├─────────────────────────────────────┤
│  Docker Compose Services:          │
│  ├── PostgreSQL + pgvector         │
│  └── Redis                         │
└─────────────────────────────────────┘
```

### Setup Steps
1. **Install dependencies on host**:
   ```bash
   # Install uv (Python package manager)
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Install Node.js (via nvm, brew, or package manager)
   # Install Claude Code (if available)
   ```

2. **Start Docker services**:
   ```bash
   docker-compose up -d db redis
   ```

3. **Setup applications**:
   ```bash
   # Backend
   cd backend
   cp .env.example .env
   uv sync
   uv run python manage.py migrate
   uv run python manage.py setup_pgvector --test-vectors

   # Frontend
   cd frontend
   npm install
   ```

## Option 3: Full Docker Development

**Best for**: Complete isolation, production-like environment

### Architecture
```
┌─────────────────────────────────────┐
│  Host System (VS Code only)        │
├─────────────────────────────────────┤
│  Docker Compose Services:          │
│  ├── PostgreSQL + pgvector         │
│  ├── Redis                         │
│  ├── Django Backend Container      │
│  ├── React Frontend Container      │
│  └── Celery Worker Container       │
└─────────────────────────────────────┘
```

### Setup
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend frontend
```

## Comparison Matrix

| Feature | DevContainer | Host + Docker | Full Docker |
|---------|-------------|---------------|-------------|
| **Claude Code Integration** | ✅ Excellent | ✅ Native | ⚠️ Limited |
| **Performance** | ✅ Good | ✅ Excellent | ⚠️ Moderate |
| **Setup Complexity** | ✅ Simple | ⚠️ Moderate | ✅ Simple |
| **Environment Consistency** | ✅ Perfect | ⚠️ Variable | ✅ Perfect |
| **Debugging** | ✅ Excellent | ✅ Excellent | ⚠️ Complex |
| **Hot Reload** | ✅ Fast | ✅ Fastest | ⚠️ Slower |
| **Resource Usage** | ⚠️ Moderate | ✅ Minimal | ❌ High |

## Migration from Current Setup

### From DevContainer to Host + Docker
```bash
# 1. Exit devcontainer
# 2. Install host dependencies (uv, Node.js)
# 3. Start only database services
docker-compose up -d db redis

# 4. Run applications on host
cd backend && uv run python manage.py runserver
cd frontend && npm run dev
```

### From Host to DevContainer
```bash
# 1. Ensure .devcontainer/ is configured
# 2. In VS Code: Reopen in Container
# 3. Wait for setup to complete
```

## Recommended Choice

### **For Claude Code Development**: DevContainer (Option 1)

**Pros**:
- Consistent environment across team members
- Claude Code works optimally in containerized environment
- Database services isolated and managed
- VS Code integration seamless
- No host system pollution

**Cons**:
- Slight performance overhead
- Requires Docker knowledge

### **For Maximum Performance**: Host + Docker Services (Option 2)

**Pros**:
- Native performance for development tools
- Direct access to host debuggers and tools
- Faster hot reload and builds
- Less resource usage

**Cons**:
- Host system dependency management
- Potential environment inconsistencies
- More setup complexity

## Current Recommendation

**Keep your DevContainer setup** and enhance it with:

1. **Optimized DevContainer**: Already configured with Python + Node.js + database clients
2. **Isolated Services**: PostgreSQL + Redis in separate containers
3. **Port Forwarding**: All services accessible on host
4. **Volume Mounts**: Code changes reflect immediately

This gives you:
- ✅ Consistent Claude Code environment
- ✅ Isolated, reproducible database setup
- ✅ Easy service management
- ✅ Team collaboration benefits
- ✅ No host system conflicts

## Quick Start Commands

### DevContainer (Recommended)
```bash
# Open VS Code in project root
code .
# Ctrl+Shift+P → "Reopen in Container"
# Wait for setup, then:
cd backend && uv run python manage.py runserver
```

### Host + Docker Services
```bash
docker-compose up -d db redis
cd backend && uv sync && uv run python manage.py runserver
cd frontend && npm install && npm run dev
```

The DevContainer approach provides the best balance of consistency, ease of use, and Claude Code integration for your development workflow.
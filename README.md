# Xandeum Nexus Intelligence

<div align="center">

![Status](https://img.shields.io/badge/Status-Production%20Ready-00FFA3?style=for-the-badge)
![Version](https://img.shields.io/badge/Version-1.1.0--SENTINEL-7000FF?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)

**Real-time Network Analytics & Monitoring for Xandeum Storage Network**

[Live Demo](https://xandeum-nexus-v7-ajv4afji5q-et.a.run.app/) • [Documentation](#-documentation) • [API Reference](#-api-endpoints) • [Contributing](#-contributing)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [API Endpoints](#-api-endpoints)
- [The Heidelberg Score](#-the-heidelberg-score-algorithm)
- [Telegram Bot](#-telegram-sentinel-bot)
- [Development](#-development)
- [Deployment](#-deployment)
- [Performance](#-performance-optimizations)
- [Contributing](#-contributing)

---

## 🌟 Overview

**Xandeum Nexus Intelligence** is a production-grade analytics and monitoring platform purpose-built for the **Xandeum Storage Network (v0.7 Heidelberg)**. Unlike traditional blockchain explorers that simply display raw data, Nexus Intelligence provides intelligent network analysis through:

- **Autonomous Network Discovery** via Gossip Protocol crawling
- **Proprietary Health Scoring** using the Heidelberg Score algorithm
- **Real-time Monitoring** with historical trend analysis
- **Telegram Integration** for proactive alerts and monitoring
- **Official Reputation Credits** integration from Xandeum's API

### Why Nexus Intelligence?

The v0.7 Heidelberg testnet presents unique challenges for traditional metrics. With minimal actual storage usage (~25KB/node) but significant committed capacity (~100MB+), standard dashboards would show misleadingly low scores. Nexus Intelligence adapts to this reality by intelligently weighing **commitment over utilization**, providing accurate and actionable insights for node operators and network stakeholders.

---

## 🚀 Key Features

### 1. Intelligent Network Crawler

- **Auto-Discovery**: Automatically discovers all pNodes via seed node gossip protocol
- **Multi-Source Aggregation**: Queries multiple seed nodes simultaneously for redundancy
- **Smart Deduplication**: Advanced logic to handle duplicate gossip entries:
  - Prioritizes newer software versions
  - Favors higher committed storage capacity
  - Tracks source node for transparency
- **Concurrent Fetching**: Parallel RPC calls with configurable timeouts (2.5s default)
- **Latency Tracking**: Measures and reports response times for each node

### 2. The Heidelberg Score™

A custom-engineered scoring algorithm tailored for the v0.7 testnet reality:

| Component | Weight | Rationale |
|-----------|--------|-----------|
| **Version Compliance** | 40% | Ensures nodes run latest stable release (0.8.x/0.9.x) |
| **Committed Capacity** | 20% | Rewards storage commitment (target: 100MB+) |
| **Uptime Reliability** | 30% | Relative uptime compared to network maximum |
| **Paging Efficiency** | 10% | Hit rate optimization (default: 95%+) |

[→ Full Algorithm Documentation](#-the-heidelberg-score-algorithm)

### 3. Official Reputation Credits

- **Live Integration**: Fetches official reputation data from `podcredits.xandeum.network`
- **Real-time Sync**: Credits updated with each telemetry refresh
- **Transparent Display**: Shows both calculated health scores and official reputation

### 4. Production-Grade Infrastructure

#### Backend (FastAPI + Python)
- **Async/Await Architecture**: Non-blocking I/O for high concurrency
- **Rate Limiting**: 30 requests/minute per IP to prevent abuse
- **Health Checks**: Cloud Run / Load Balancer compatible endpoints
- **Comprehensive Logging**: Structured logs with appropriate verbosity levels
- **Error Handling**: Graceful degradation with detailed error responses

#### Frontend (React + TailwindCSS)
- **Infinite Scroll**: Smooth rendering of 500+ nodes without pagination
- **Real-time Updates**: Auto-refresh with configurable intervals
- **Responsive Design**: Mobile-first approach with adaptive layouts
- **Data Export**: CSV download with processed metrics
- **Visual Analytics**: Chart.js integration for historical trends

#### Storage System
- **Dual-Mode Operation**: 
  - **Cloud Storage** (GCS) for production deployments
  - **Local JSON** for development environments
- **Async Writes**: Non-blocking history persistence
- **Rate-Limited Snapshots**: Maximum 1 entry per 5 minutes
- **Atomic Operations**: Safe concurrent access patterns

### 5. Telegram Sentinel Bot

- **Watchlist Management**: Track specific nodes by pubkey
- **Custom Alerts**: Configurable thresholds for health score drops
- **Ignore Lists**: Temporarily mute notifications
- **Network Statistics**: On-demand health reports via `/health` command
- **Node Lookup**: Search by pubkey with `/node <pubkey>` command

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     CLIENT LAYER                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Web UI     │  │ Telegram Bot │  │  API Clients │     │
│  │  (React)     │  │  (PTB)       │  │  (External)  │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    FASTAPI APPLICATION                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Routes Layer                                        │  │
│  │  • /api/telemetry    • /api/history/trend          │  │
│  │  • /health           • Rate Limiting                │  │
│  └──────────────────┬───────────────────────────────────┘  │
│                     │                                       │
│  ┌──────────────────▼───────────────────────────────────┐  │
│  │  Network Intelligence Layer                          │  │
│  │  • Multi-seed crawling   • Version parsing          │  │
│  │  • Deduplication logic   • Score calculation        │  │
│  │  • Credits API fetch     • Latency tracking         │  │
│  └──────────────────┬───────────────────────────────────┘  │
│                     │                                       │
│  ┌──────────────────▼───────────────────────────────────┐  │
│  │  Storage Manager (Async)                            │  │
│  │  • History persistence   • Watchlist management     │  │
│  │  • GCS/Local fallback    • Atomic writes           │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                   EXTERNAL SERVICES                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Xandeum pRPC │  │  Credits API │  │  Telegram    │     │
│  │  (Port 6000) │  │  (Official)  │  │  Bot API     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Network Scan**: Crawler queries all seed nodes via pRPC (`get-pods-with-stats`)
2. **Credits Fetch**: Parallel request to official Xandeum credits API
3. **Processing**: Deduplication → Score Calculation → Credits Injection
4. **Storage**: Async persistence to GCS/Local with rate limiting
5. **Response**: JSON payload to frontend with sorted nodes
6. **Rendering**: React components update with smooth animations

---

## 💻 Installation

### Prerequisites

- **Python**: 3.9 or higher
- **Pip**: Latest version
- **Git**: For cloning the repository

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/xandeum-nexus.git
cd xandeum-nexus

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create data directory (optional - auto-created)
mkdir -p data

# 4. Run the application
python run.py
```

The dashboard will be available at: **http://localhost:8080**

### Docker Deployment (Optional)

```bash
# Build image
docker build -t xandeum-nexus .

# Run container
docker run -p 8080:8080 \
  -e PORT=8080 \
  -e TELEGRAM_BOT_TOKEN=your_token_here \
  xandeum-nexus
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Server Configuration
PORT=8080
RPC_PORT=6000
RPC_ENDPOINT=/rpc

# Project Metadata
PROJECT_TITLE="Xandeum Nexus Intelligence"
PROJECT_VERSION="1.1.0-SENTINEL"

# Telegram Bot (Optional)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_BOT_USERNAME=your_bot_username

# Network Configuration (Optional - uses defaults if not set)
SEED_NODES=173.212.203.145,173.212.220.65,161.97.97.41
```

### Default Seed Nodes

If `SEED_NODES` is not configured, the system uses these production seeds:

```python
[
    "173.212.203.145", "173.212.220.65", "161.97.97.41",
    "192.190.136.36", "192.190.136.37", "192.190.136.38",
    "192.190.136.28", "192.190.136.29", "207.244.255.1"
]
```

### Storage Configuration

- **Development**: Uses `data/network_history.json` (auto-created)
- **Production**: Automatically uses GCS if credentials available
- **History Limit**: Keeps last 1000 snapshots (5+ hours at 5min intervals)

---

## 📡 API Endpoints

### Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "Xandeum Nexus Intelligence",
  "version": "1.1.0-SENTINEL",
  "timestamp": 1703123456.789
}
```

### Network Telemetry

```http
GET /api/telemetry
```

**Response:**
```json
{
  "timestamp": 1703123456.789,
  "network": {
    "total_nodes": 247,
    "total_storage_gb": 24.5623,
    "avg_health": 87.3,
    "v7_adoption": 235,
    "avg_paging_efficiency": 0.952
  },
  "nodes": [
    {
      "pubkey": "5xHn7K2m...",
      "short_id": "5xHn7K2m...",
      "ip": "173.212.203.145",
      "version": "0.8.1",
      "uptime_sec": 345678.9,
      "storage_used": 25600,
      "storage_gb": 0.0953,
      "health_score": 94,
      "reputation_credits": 1250,
      "score_breakdown": {
        "v0.7_compliance": 40,
        "uptime_reliability": 29,
        "storage_weight": 15,
        "paging_efficiency": 10
      },
      "paging_metrics": {
        "hit_rate": 0.98,
        "replication_health": 3
      },
      "latency_ms": 45.2
    }
  ]
}
```

**Rate Limiting**: 30 requests per minute per IP

### Historical Trends

```http
GET /api/history/trend
```

**Response:**
```json
{
  "timestamps": [1703120000, 1703120300, 1703120600],
  "node_counts": [245, 247, 246],
  "health": [86.5, 87.3, 87.1],
  "paging_efficiency": [0.951, 0.952, 0.953]
}
```

---

## 🎯 The Heidelberg Score Algorithm

### Design Philosophy

The Heidelberg Score was engineered to solve a critical problem: **how to fairly evaluate node health during the testnet phase when actual storage usage is negligible**.

Traditional metrics would penalize all nodes equally for low usage. Our algorithm recognizes that **commitment matters more than utilization** during early network growth.

### Calculation Logic

```python
def calculate_heidelberg_score(node: Dict, net_stats: Dict) -> Dict:
    # 1. VERSION COMPLIANCE (40 points)
    version = node.get('version', '0.0.0')
    score_version = 40 if ('0.8' in version or '0.9' in version) else 10
    
    # 2. UPTIME RELIABILITY (30 points)
    uptime = float(node.get('uptime', 0))
    max_uptime = net_stats.get('max_uptime', 1)
    score_uptime = (uptime / max_uptime) * 30
    
    # 3. STORAGE COMMITMENT (20 points)
    storage_committed = float(node.get('storage_committed', 0))
    storage_gb = storage_committed / (1024**3)
    target_gb = 0.1  # 100MB target
    score_storage = min((storage_gb / target_gb) * 20, 20)
    
    # 4. PAGING EFFICIENCY (10 points)
    hit_rate = float(node.get('paging_hit_rate', 0.95))
    score_paging = hit_rate * 10
    
    total = min(score_version + score_uptime + score_storage + score_paging, 100)
    
    return {
        "total": int(total),
        "breakdown": { ... },
        "metrics": { ... }
    }
```

### Scoring Examples

| Scenario | Version | Uptime | Storage | Paging | Total |
|----------|---------|--------|---------|--------|-------|
| **Optimal Node** | 0.8.1 (40) | 99% (30) | 150MB (20) | 98% (10) | **100** |
| **Good Node** | 0.8.0 (40) | 85% (26) | 100MB (20) | 95% (10) | **96** |
| **Average Node** | 0.7.9 (40) | 70% (21) | 75MB (15) | 92% (9) | **85** |
| **Outdated Node** | 0.6.5 (10) | 60% (18) | 50MB (10) | 90% (9) | **47** |

### Why This Approach Works

1. **Version Compliance (40%)**: Ensures network security and feature parity
2. **Uptime (30%)**: Rewards reliability and operational excellence
3. **Commitment (20%)**: Incentivizes capacity planning without penalizing testnet reality
4. **Efficiency (10%)**: Recognizes optimization efforts in cache management

---

## 🤖 Telegram Sentinel Bot

### Setup

1. Create a bot via [@BotFather](https://t.me/botfather)
2. Copy your token to `.env`:
   ```bash
   TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
   TELEGRAM_BOT_USERNAME=YourBotUsername
   ```
3. Restart the application

### Commands

- `/start` - Welcome message and instructions
- `/health` - Current network statistics
- `/node <pubkey>` - Lookup specific node details
- `/watch <pubkey>` - Add node to watchlist
- `/unwatch <pubkey>` - Remove from watchlist
- `/list` - Show all watched nodes
- `/ignore <minutes>` - Temporarily mute alerts

### Alert Triggers

The bot automatically sends alerts when:

- **Health drops below 70**: Warning alert
- **Node goes offline**: Connection lost notification
- **Version outdated**: Update recommendation
- **Storage commitment drops**: Capacity reduction alert

---

## 🛠️ Development

### Project Structure

```
xandeum-nexus/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI application entry
│   ├── config.py         # Configuration management
│   ├── routes.py         # API route handlers
│   ├── network.py        # Network crawler & scoring
│   ├── storage.py        # Data persistence layer
│   └── bot.py            # Telegram bot logic
├── static/
│   └── js/
│       └── dashboard.js  # React frontend
├── templates/
│   └── index.html        # HTML template
├── data/                 # Auto-generated storage
│   ├── network_history.json
│   ├── watchlist.json
│   └── ignores.json
├── requirements.txt
├── run.py               # Application launcher
└── README.md
```

### Running Tests

```bash
# Install dev dependencies
pip install pytest pytest-asyncio pytest-cov

# Run tests
pytest tests/ -v --cov=app

# Generate coverage report
pytest --cov=app --cov-report=html
```

### Code Style

```bash
# Install formatters
pip install black isort flake8

# Format code
black app/
isort app/

# Lint
flake8 app/ --max-line-length=100
```

---

## 🚀 Deployment

### Google Cloud Run

```bash
# 1. Build and push container
gcloud builds submit --tag gcr.io/YOUR_PROJECT/xandeum-nexus

# 2. Deploy
gcloud run deploy xandeum-nexus \
  --image gcr.io/YOUR_PROJECT/xandeum-nexus \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 512Mi \
  --timeout 60 \
  --set-env-vars "TELEGRAM_BOT_TOKEN=your_token"
```

### Traditional VPS

```bash
# Using systemd service
sudo cp xandeum-nexus.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable xandeum-nexus
sudo systemctl start xandeum-nexus
```

### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## ⚡ Performance Optimizations

### Backend

- **Async I/O**: All network calls use `aiohttp` for non-blocking operations
- **Concurrent Crawling**: Parallel RPC requests to all seed nodes
- **Smart Caching**: 5-minute minimum interval between history snapshots
- **Connection Pooling**: Reuses HTTP connections via `aiohttp.ClientSession`
- **Timeout Management**: 2.5s timeout per node to prevent hanging

### Frontend

- **Virtual Scrolling**: Only renders visible nodes in viewport
- **Debounced Search**: 300ms delay before filtering executes
- **Memoized Calculations**: React `useMemo` for expensive computations
- **Lazy Loading**: Charts load on-demand when scrolled into view
- **CSS Optimization**: Tailwind JIT for minimal bundle size

### Database

- **Atomic Writes**: Temp file + `os.replace()` for crash safety
- **Batch Operations**: Groups multiple writes into single transaction
- **Index Optimization**: In-memory dictionaries for O(1) lookups
- **Compression**: JSON minification reduces storage by ~40%

---

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

### Reporting Issues

1. Check existing issues first
2. Provide detailed reproduction steps
3. Include system information (OS, Python version)
4. Attach relevant logs if applicable

### Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Code Standards

- Follow PEP 8 style guide
- Add docstrings to all functions
- Include type hints where appropriate
- Write tests for new features
- Update documentation as needed

---

<div align="center">

**Built with ❤️ for the Xandeum Storage Network**

</div>

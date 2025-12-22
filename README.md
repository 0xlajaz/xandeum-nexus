# 🛡️ Xandeum Nexus Intelligence

> **Real-time Analytics Platform for Xandeum pNodes** • Built for the Xandeum Storage Network Bounty

[![Live Demo](https://img.shields.io/badge/🌐_Live_Demo-Visit_Now-00FFA3?style=for-the-badge)](https://xandeum-nexus-1051632639521.us-central1.run.app)
[![Version](https://img.shields.io/badge/version-1.1.0--SENTINEL-blue?style=for-the-badge)](https://github.com/yourusername/xandeum-nexus)
[![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)](LICENSE)

---

## 🎯 Overview

**Xandeum Nexus Intelligence** is a comprehensive analytics platform designed to monitor, analyze, and visualize the health of Xandeum's decentralized storage network. Built for node operators, validators, and network enthusiasts, it provides real-time insights into pNode performance with enterprise-grade monitoring capabilities.

### 🌟 What Makes This Special?

- **🔴 Real-time Network Monitoring**: Live data from gossip protocol across all seed nodes
- **📊 Intelligent Health Scoring**: Proprietary "Heidelberg Algorithm" for multi-dimensional node analysis
- **🤖 24/7 Telegram Sentinel Bot**: Smart alerts with severity-based notification intervals
- **🗺️ Geographic Insights**: Visual network distribution with MaxMind GeoIP integration
- **📈 Historical Analytics**: Trend analysis with time-series data visualization
- **⚡ Enterprise Performance**: Deployed on Google Cloud Run with auto-scaling

---

## 🎥 Demo Video

> 📹 **Watch the full walkthrough**:

[![Xandeum Nexus Demo](https://img.shields.io/badge/▶️_Watch_Demo-YouTube-red?style=for-the-badge)](YOUR_VIDEO_LINK_HERE)

### Quick Preview

```bash
# Live Dashboard Access
https://xandeum-nexus-1051632639521.us-central1.run.app

# Features Showcased:
✅ Real-time node health monitoring
✅ Interactive data tables with search/filter
✅ Historical trend charts
✅ Telegram bot commands
✅ CSV export functionality
```

---

## ✨ Key Features

### 🎛️ **Dashboard Analytics**
- **Real-time Telemetry**: Live updates every 5 minutes from 9 seed nodes
- **Health Scoring System**: 100-point scale based on version, uptime, storage, and paging efficiency
- **Smart Filtering**: View all nodes, v0.8+ compliant, or nodes with issues
- **Advanced Search**: Filter by pubkey, IP address, city, or country
- **CSV Export**: Download complete node data for offline analysis

### 🤖 **Telegram Sentinel Bot**
The intelligent monitoring assistant that never sleeps:

```
📱 Available Commands:
/start        - Initialize dashboard
/watch <id>   - Monitor a specific node
/check <id>   - Detailed health analysis
/list         - View your watchlist
/stats        - Network-wide statistics
/stop <id>    - Remove node from monitoring
/help         - Command reference
```

**Smart Alert System:**
- 🔴 CRITICAL → Alert every 1 hour
- 🟡 WARNING → Alert every 6 hours
- ⚫️ OFFLINE → Alert every 10 minutes
- 🟢 RECOVERY → Immediate notification
- 💤 Snooze functionality (24 hours)
- 🔇 Permanent ignore for non-critical issues

### 📊 **Heidelberg Health Score**

Our proprietary algorithm evaluates nodes across 4 dimensions:

| Metric | Weight | Criteria |
|--------|--------|----------|
| **Version Compliance** | 40 pts | v0.8+ required |
| **Uptime Reliability** | 30 pts | Normalized against network max |
| **Storage Capacity** | 20 pts | Target: 100MB minimum |
| **Paging Efficiency** | 10 pts | Cache hit rate optimization |

**Total**: 100 points • **Excellent**: 90+ • **Good**: 75-89 • **Fair**: 50-74 • **Poor**: <50

### 🌍 **Geographic Distribution**

- **Real-time Geo-mapping**: MaxMind GeoLite2 database for zero-latency lookups
- **Privacy-preserving**: All IP resolution happens locally
- **Top 5 Locations**: Displayed on dashboard with node counts
- **Visibility Tracking**: Multi-witness consensus validation

### 📈 **Historical Analytics**

- **Time-series Storage**: Up to 1000 data points per metric
- **Trend Visualization**: Network health over time
- **Metrics Tracked**:
  - Total active nodes
  - Average health score
  - Storage capacity trends
  - Paging efficiency evolution

---

## 🏗️ Technical Architecture

### **Backend Stack**

```python
FastAPI Framework          # High-performance async API
├── Network Layer          # Async gossip protocol scanning
│   ├── aiohttp           # Concurrent RPC calls
│   ├── GeoIP Resolution  # MaxMind GeoLite2
│   └── Credits API       # Official reputation integration
├── Data Layer            
│   ├── JSON Storage      # Flat-file persistence
│   └── Async I/O         # Non-blocking disk operations
└── Bot Layer
    ├── python-telegram-bot v20
    └── Smart Alert Engine
```

### **Frontend Stack**

```javascript
React 18                   # Modern UI framework
├── Real-time Updates      # Auto-refresh every 5 min
├── Responsive Design      # Mobile-first approach
└── Data Visualization     # Chart.js integration
```

### **Infrastructure**

- **Hosting**: Google Cloud Run (us-central1)
- **Auto-scaling**: 0-10 instances based on traffic
- **Rate Limiting**: 30 requests/minute per IP
- **Security**: CORS configured, request validation
- **Monitoring**: Structured logging with severity levels

---

## 🚀 Getting Started

### Prerequisites

```bash
Python 3.11+
Node.js 18+ (for frontend development)
Telegram Bot Token (for bot features)
MaxMind GeoLite2 Database (optional, for geo features)
```

### Installation

1. **Clone the Repository**
```bash
git clone https://github.com/yourusername/xandeum-nexus.git
cd xandeum-nexus
```

2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure Environment**
```bash
cp .env.example .env
# Edit .env with your settings:
# TELEGRAM_BOT_TOKEN=your_token_here
# TELEGRAM_BOT_USERNAME=your_bot_username
# PORT=8080
```

4. **Setup GeoIP Database** (Optional)
```bash
# Download MaxMind GeoLite2-City database
mkdir -p data
# Place GeoLite2-City.mmdb in data/ directory
```

5. **Run the Application**
```bash
# Development
uvicorn app.main:app --reload --port 8080

# Production
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8080
```

6. **Access Dashboard**
```
http://localhost:8080
```

---

## 📡 API Documentation

### GET `/health`
Health check endpoint for load balancers.

**Response:**
```json
{
  "status": "healthy",
  "service": "Xandeum Nexus Intelligence",
  "version": "1.1.0-SENTINEL",
  "timestamp": 1703001234.56
}
```

### GET `/api/telemetry`
Retrieve real-time network state.

**Response:**
```json
{
  "timestamp": 1703001234.56,
  "network": {
    "total_nodes": 42,
    "total_storage_gb": 1234.56,
    "avg_health": 87.3,
    "v7_adoption": 38,
    "avg_paging_efficiency": 0.92,
    "geo_distribution": {
      "US|New York": 12,
      "DE|Frankfurt": 8
    }
  },
  "nodes": [
    {
      "pubkey": "5xHn7K2mPxQ9vK8...",
      "short_id": "5xHn7K2m...",
      "ip": "173.212.203.145",
      "version": "0.8.1",
      "uptime_sec": 86400,
      "storage_gb": 0.1,
      "health_score": 95,
      "reputation_credits": 1500,
      "score_breakdown": {
        "v0.7_compliance": 40,
        "uptime_reliability": 30,
        "storage_weight": 20,
        "paging_efficiency": 10
      },
      "paging_metrics": {
        "hit_rate": 0.95,
        "replication_health": 3
      },
      "geo": {
        "country": "United States",
        "countryCode": "US",
        "city": "New York"
      }
    }
  ]
}
```

**Rate Limit:** 30 requests/minute per IP

### GET `/api/history/trend`
Historical network metrics for charting.

**Response:**
```json
{
  "timestamps": [1703001234, 1703001534, ...],
  "node_counts": [42, 43, ...],
  "health": [87.3, 88.1, ...],
  "paging_efficiency": [0.92, 0.93, ...]
}
```

---

## 🤖 Telegram Bot Setup

1. **Create Bot with BotFather**
```
/newbot
Name: Xandeum Sentinel
Username: @YourSentinelBot
```

2. **Configure Token**
```bash
# Add to .env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_BOT_USERNAME=YourSentinelBot
```

3. **Start Monitoring**
```
Open Telegram → Search @YourSentinelBot → /start
/watch 5xHn7K2mPxQ9vK8...
```

---

## 📊 Project Statistics

| Metric | Value |
|--------|-------|
| **Lines of Code** | ~3,500+ |
| **API Endpoints** | 3 core + health check |
| **Bot Commands** | 7 commands |
| **Data Points Tracked** | 15+ per node |
| **Update Interval** | 5 minutes |
| **Max History Storage** | 1,000 snapshots |
| **Rate Limit** | 30 req/min/IP |

---

## 🎨 Screenshots

### Main Dashboard
![Dashboard Overview](screenshots/dashboard.png)
*Real-time network monitoring with health scores and geographic distribution*

### Node Details
![Node Details](screenshots/node-details.png)
*Comprehensive node analysis with score breakdown and diagnostics*

### Telegram Bot
![Telegram Bot](screenshots/telegram-bot.png)
*Smart alerts and interactive commands*

### Historical Trends
![Trends Chart](screenshots/trends.png)
*Network health evolution over time*

> 📝 **Note**: Add screenshots to `/screenshots` directory

---

## 🏆 Bounty Submission Details

### Superteam Xandeum Analytics Platform Bounty

**Submission Checklist:**
- ✅ Live, functional website with pRPC integration
- ✅ Real-time pNode data retrieval from gossip protocol
- ✅ Clear, intuitive data presentation
- ✅ Advanced features (Telegram bot, health scoring, geo tracking)
- ✅ Documentation and deployment guide
- ✅ Open-source codebase

**Judging Criteria Alignment:**
- **Functionality**: ✅ Successfully retrieves and displays all pNode data using valid pRPC calls
- **Clarity**: ✅ Health scoring system, color-coded status indicators, comprehensive tooltips
- **User Experience**: ✅ Intuitive dashboard, mobile-responsive, real-time updates, search/filter
- **Innovation**: ✅ Proprietary Heidelberg scoring, Telegram bot integration, geographic insights, historical analytics

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Workflow

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Xandeum Labs** - For building an innovative storage layer for Solana
- **Superteam** - For organizing the bounty program
- **MaxMind** - For GeoLite2 database
- **Telegram** - For the Bot API
- **Open Source Community** - For amazing tools and libraries

---

## 🔗 Links

- **Live Dashboard**: [xandeum-nexus-1051632639521.us-central1.run.app](https://xandeum-nexus-1051632639521.us-central1.run.app)
- **Xandeum Network**: [xandeum.network](https://xandeum.network)
- **Xandeum Documentation**: [docs.xandeum.network](https://docs.xandeum.network)
- **Xandeum Discord**: [discord.gg/uqRSmmM5m](https://discord.gg/uqRSmmM5m)
- **Superteam**: [superteam.fun](https://superteam.fun)

---

## 📧 Contact

**Project Maintainer**: [Wade]
- Twitter: [@yourhandle](https://twitter.com/0xlajaz)
- GitHub: [@yourusername](https://github.com/0xlajaz)
- Discord: 0xlajaz

---

<div align="center">

### ⭐ Star this repository if you find it useful!

**Built with ❤️ for the Xandeum Community**

[![Made with FastAPI](https://img.shields.io/badge/Made%20with-FastAPI-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=white)](https://reactjs.org/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org/)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-26A5E4?style=flat-square&logo=telegram)](https://telegram.org/)

</div>

# Xandeum Nexus Intelligence

![Status](https://img.shields.io/badge/Status-Production%20Ready-00FFA3?style=for-the-badge&logoColor=black)
![Version](https://img.shields.io/badge/Heidelberg-v0.7-7000FF?style=for-the-badge)
![Tech](https://img.shields.io/badge/FastAPI-React-black?style=for-the-badge&logo=python)

**Xandeum Nexus Intelligence** is a production-grade analytics platform designed specifically for the **Xandeum Storage Network (v0.7 Heidelberg)**.

Unlike standard blockchain explorers that merely list raw data, Nexus Intelligence implements a specialized **"Heidelberg Score"** algorithm to evaluate pNode health. It intelligently adapts to the current testnet phase by rewarding **Capacity Commitment** rather than raw usage, providing a fair, accurate, and visually meaningful representation of the network's potential.

### 🚀 **Live Demo:** [https://xandeum-nexus-v7-ajv4afji5q-et.a.run.app/](https://xandeum-nexus-v7-ajv4afji5q-et.a.run.app/)

---

## 🏆 Key Features

### 1. Intelligent Gossip Crawler
* **Auto-Discovery:** Automatically crawls public seed nodes to discover the entire pNode topology via the Gossip Protocol (`pRPC`).
* **Smart Deduplication:** Implements advanced logic to handle duplicate gossip entries across the network, ensuring unique node identity by prioritizing newer versions and higher committed storage.

### 2. The "Heidelberg Score" Algorithm 
We engineered a custom scoring model tailored to the **v0.7 Testnet**. Since the network is in its early stages (pre-mainnet), actual storage usage is negligible (~25KB/node). Standard metrics would result in a "zero score" for everyone. Our algorithm rewards **Committed Capacity** to reflect the true value provided by node operators.

| Metric | Weight | Description |
| :--- | :--- | :--- |
| **Version Compliance** | **40 pts** | Validates if the node is running the latest stable release (v0.7.x / v0.8.x). |
| **Committed Capacity** | **20 pts** | Scores based on `storage_committed` (Capacity) rather than `storage_used`. Target: >100MB (Adjusted for Testnet). |
| **Uptime Stability** | **30 pts** | Relative score compared to the highest uptime in the cluster. |
| **Paging Efficiency** | **10 pts** | Measures the **Hit Rate** efficiency of the node's paging system. |

### 3. Production-Grade Architecture
* **Hybrid Storage System (Cloud + Local):**
    * **Cloud Mode:** Automatically connects to Google Cloud Storage (GCS) when deployed, ensuring data persistence across container restarts.
    * **Local Mode:** Seamlessly falls back to `local_history.json` for easy development without needing Cloud credentials.
* **Rate Limiting:** Protects the database from "Observer Effect" spam by limiting historical snapshots to once every 5 minutes.
* **Infinite Scroll UI:** A high-performance React frontend capable of rendering hundreds of nodes smoothly without pagination lag.

---

## 🛠️ Installation & Local Development

Xandeum Nexus is open-source and designed to run anywhere. You do not need a Google Cloud account to run it locally.

### Prerequisites
* Python 3.9+
* Pip

### 1. Clone the Repository
```bash
git clone https://github.com/0xlajaz/xandeum-nexus.git
cd xandeum-nexus
```
### 2. Install Dependencies
```bash
pip install -r requirements.txt
```
### 3. Run the Application
```bash
python run.py
```
### 4. Access Dashboard
Open your browser and visit: http://localhost:8080

---

## 🔍 Submission Notes for Judges
### Why "Committed" over "Used"?
According to the **v0.7 Heidelberg** documentation, current network nodes exhibit negligible storage usage (~25KB) relative to their committed capacity (~100MB). To provide a fair and meaningful health score, our dashboard prioritizes **Committed Capacity**. This accurately reflects the network's potential health during this early testnet phase.

### CSV Export Accuracy
The data export feature provides cleaned and processed metrics (converting raw Bytes to GB), ensuring that the downloaded data matches the visual dashboard metrics (e.g., a Score of 99 correlates with High Capacity in the CSV).

---

<p align="center"> Built with ❤️ for the <b>Xandeum Superteam Bounty</b> </p>

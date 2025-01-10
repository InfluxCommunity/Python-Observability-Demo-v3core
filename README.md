# Python Observability Dashboard using InfluxDB 3 Core

## 🌟 Overview

A comprehensive system observability dashboard built with Python (Flask), InfluxDB 3 Core providing real-time system metrics and performance insights.

## ✨ Features

- Real-time system metrics visualization
- CPU, Memory, Network, and Disk I/O tracking
- Process monitoring
- Time-series metrics storage with InfluxDB
- Lightweight and extensible observability solution

## Prerequisites

- Python 3.10+
- InfluxDB 3 Core
- macOS, Linux, or Windows

## Technology Stack

- **Backend**: Flask
- **Metrics Database**: InfluxDB v3
- **System Metrics**: psutil
- **Frontend**: Chart.js
- **Visualization**: Real-time web dashboard

## 🛠 Setup, Install & Run

### 1. Clone the Repository

```bash
git clone https://github.com/InfluxCommunity/Python-Observability-Demo-v3core/tree/main
cd Python-Observability-Demo-v3core
```

### 2. Create Virtual Enviornment

```bash
# Using built-in venv
python3 -m venv .venv
```

### 3. Activate the virtual environment

```
source .venv/bin/activate
```

### 4. Install dependencies including InfluxDB 3 Core

```bash
pip install -r requirements.txt
```

##### Download InfluxDB 3 Core shell script and run it to install the database

```
sh install_InfluxDB_3_Core.sh
```

### 5. Run the app

```bash
python app.py
```

Open your web browser and navigate to: http://localhost:5000

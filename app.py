from flask import Flask, render_template, Response
from influx_metrics import influx_metrics
import time
import logging
import traceback
import json
import psutil
import threading
import queue
import platform
import subprocess

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Create a thread-safe queue for metrics
metrics_queue = queue.Queue(maxsize=50)

def get_network_io():
    """Get network I/O statistics"""
    try:
        # Get the primary network interface
        net_io = psutil.net_io_counters()
        return {
            'bytes_sent': net_io.bytes_sent / (1024 * 1024),  # Convert to MB
            'bytes_recv': net_io.bytes_recv / (1024 * 1024),  # Convert to MB
            'packets_sent': net_io.packets_sent,
            'packets_recv': net_io.packets_recv
        }
    except Exception as e:
        logger.error(f"Network metrics error: {e}")
        return {
            'bytes_sent': 0,
            'bytes_recv': 0,
            'packets_sent': 0,
            'packets_recv': 0
        }

def get_disk_io():
    """Get disk I/O statistics"""
    try:
        disk_io = psutil.disk_io_counters()
        return {
            'read_bytes': disk_io.read_bytes / (1024 * 1024),  # Convert to MB
            'write_bytes': disk_io.write_bytes / (1024 * 1024),  # Convert to MB
            'read_count': disk_io.read_count,
            'write_count': disk_io.write_count
        }
    except Exception as e:
        logger.error(f"Disk metrics error: {e}")
        return {
            'read_bytes': 0,
            'write_bytes': 0,
            'read_count': 0,
            'write_count': 0
        }

def collect_metrics_thread():
    """Background thread to collect system metrics"""
    while True:
        try:
            # Collect system metrics
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            network_io = get_network_io()
            disk_io = get_disk_io()
            
            # Create metrics payload
            metrics = {
                'timestamp': time.time(),
                'cpu_usage': cpu_percent,
                'memory_usage': memory.percent,
                'memory_total': memory.total / (1024 * 1024 * 1024),  # Convert to GB
                'memory_available': memory.available / (1024 * 1024 * 1024),  # Convert to GB
                'memory_used': memory.used / (1024 * 1024 * 1024),  # Convert to GB
                'network_bytes_sent': network_io['bytes_sent'],
                'network_bytes_recv': network_io['bytes_recv'],
                'disk_read_bytes': disk_io['read_bytes'],
                'disk_write_bytes': disk_io['write_bytes']
            }
            
            # Write to InfluxDB
            influx_metrics.collect_system_metrics()
            
            # Add to queue, remove oldest if full
            if metrics_queue.full():
                metrics_queue.get()
            metrics_queue.put(metrics)
            
            # Wait before next collection
            time.sleep(1)
        except Exception as e:
            logger.error(f"Metrics collection error: {e}")
            time.sleep(5)

@app.route('/')
def index():
    return render_template('realtime_metrics.html')

@app.route('/metrics-stream')
def metrics_stream():
    def event_stream():
        while True:
            try:
                # Wait for new metrics
                metrics = metrics_queue.get(timeout=1)
                yield f"data: {json.dumps(metrics)}\n\n"
            except queue.Empty:
                # No new metrics, send a comment to keep connection alive
                yield ":heartbeat\n\n"
            except Exception as e:
                logger.error(f"Stream error: {e}")
                break
    
    return Response(event_stream(), mimetype='text/event-stream')

@app.route('/system-info')
def system_info():
    """Provide detailed system information"""
    try:
        return jsonify({
            'platform': platform.system(),
            'platform_release': platform.release(),
            'platform_version': platform.version(),
            'architecture': platform.machine(),
            'processor': platform.processor(),
            'cpu_count': psutil.cpu_count(logical=False),  # Physical CPUs
            'cpu_count_logical': psutil.cpu_count(logical=True),  # Logical CPUs
            'total_memory': psutil.virtual_memory().total / (1024 * 1024 * 1024),  # GB
        })
    except Exception as e:
        logger.error(f"System info error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/process-metrics')
def process_metrics():
    """Get top resource-consuming processes"""
    try:
        # Get process information
        processes = []
        for proc in sorted(psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']), 
                           key=lambda x: x.info['cpu_percent'], 
                           reverse=True)[:10]:
            try:
                processes.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'cpu_percent': proc.info['cpu_percent'],
                    'memory_percent': proc.info['memory_percent']
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        return jsonify(processes)
    except Exception as e:
        logger.error(f"Process metrics error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/disk-usage')
def disk_usage():
    """Get disk usage information"""
    try:
        disk_partitions = psutil.disk_partitions()
        disk_info = []
        
        for partition in disk_partitions:
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disk_info.append({
                    'device': partition.device,
                    'mountpoint': partition.mountpoint,
                    'fstype': partition.fstype,
                    'total_size': usage.total / (1024 * 1024 * 1024),  # GB
                    'used': usage.used / (1024 * 1024 * 1024),  # GB
                    'free': usage.free / (1024 * 1024 * 1024),  # GB
                    'percent': usage.percent
                })
            except Exception as e:
                logger.error(f"Disk usage error for {partition.mountpoint}: {e}")
        
        return jsonify(disk_info)
    except Exception as e:
        logger.error(f"Disk usage overall error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/network-connections')
def network_connections():
    """Get active network connections"""
    try:
        connections = []
        for conn in psutil.net_connections():
            try:
                connections.append({
                    'fd': conn.fd,
                    'family': str(conn.family),
                    'type': str(conn.type),
                    'laddr': str(conn.laddr),
                    'raddr': str(conn.raddr),
                    'status': conn.status
                })
            except Exception as e:
                logger.error(f"Network connection error: {e}")
        
        return jsonify(connections)
    except Exception as e:
        logger.error(f"Network connections error: {e}")
        return jsonify({'error': str(e)}), 500

# Query endpoints for InfluxDB metrics
@app.route('/query/system-metrics')
def query_system_metrics():
    """Query system metrics from InfluxDB"""
    try:
        # Example query for system metrics
        table = influx_metrics.client.query(
            query="SELECT * FROM system_metrics ORDER BY time DESC LIMIT 100",
            language="sql"
        )
        return jsonify({
            'schema': str(table.schema),
            'data': table.to_pydict()
        })
    except Exception as e:
        logger.error(f"System metrics query error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/metrics-overview')
def metrics_overview():
    """Provide an overview of available metrics and endpoints"""
    return jsonify({
        'available_endpoints': [
            '/system-info',
            '/process-metrics',
            '/disk-usage',
            '/network-connections',
            '/query/system-metrics',
            '/metrics-stream'
        ],
        'dashboard': '/realtime-metrics'
    })
    
if __name__ == '__main__':
    # Start metrics collection thread
    metrics_thread = threading.Thread(target=collect_metrics_thread, daemon=True)
    metrics_thread.start()
    
    try:
        app.run(debug=True, threaded=True)
    except Exception as e:
        logger.error(f"Application startup error: {e}")
        logger.error(traceback.format_exc())
    finally:
        # Ensure InfluxDB client is closed
        influx_metrics.close()
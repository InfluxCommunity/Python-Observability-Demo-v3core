import os
import logging
from dotenv import load_dotenv
from influxdb_client_3 import InfluxDBClient3, Point
import psutil
import time

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class InfluxMetricsCollector:
    def __init__(self):
        # Create InfluxDB client
        try:
            # Try connection without any additional parameters
            self.client = InfluxDBClient3(
                host='http://127.0.0.1:8181',
                database='localhost'
            )
            logger.info("InfluxDB client created successfully")
        except Exception as e:
            logger.error(f"Failed to create InfluxDB client: {e}")
            raise

    def collect_system_metrics(self):
        """Collect system-level metrics"""
        try:
            # CPU Usage
            cpu_percent = psutil.cpu_percent()
            
            # Memory Usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Create InfluxDB point
            point = Point("system_metrics") \
                .tag("host", "local_macbook") \
                .field("cpu_usage", float(cpu_percent)) \
                .field("memory_usage", float(memory_percent))
            
            # Write to InfluxDB
            self.client.write(point)
            logger.info(f"System metrics collected - CPU: {cpu_percent}%, Memory: {memory_percent}%")
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            raise

    def log_web_metrics(self, endpoint, response_time):
        """Log web application metrics"""
        try:
            point = Point("web_metrics") \
                .tag("endpoint", endpoint) \
                .field("response_time", float(response_time))
            
            self.client.write(point)
            logger.info(f"Web metrics logged - Endpoint: {endpoint}, Response Time: {response_time}ms")
        except Exception as e:
            logger.error(f"Failed to log web metrics: {e}")
            raise

    def query_metrics(self, measurement, limit=10):
        """Query metrics from InfluxDB using SQL"""
        try:
            table = self.client.query(
                query=f"SELECT * FROM {measurement} LIMIT {limit}",
                language="sql"
            )
            return table
        except Exception as e:
            logger.error(f"Failed to query metrics: {e}")
            raise

    def get_metric_measurements(self):
      """Get available measurements using SQL"""
      try:
          # Instead of using a generic SQL approach, query the specific measurement
          table = self.client.query(
              query="SELECT host, cpu_usage, memory_usage FROM system_metrics LIMIT 5",
              language="sql"
          )
          return table
      except Exception as e:
          logger.error(f"Failed to get measurements: {e}")
          raise

    def close(self):
        """Close InfluxDB client"""
        try:
            self.client.close()
            logger.info("InfluxDB client closed")
        except Exception as e:
            logger.error(f"Error closing InfluxDB client: {e}")

# Create a global instance
influx_metrics = InfluxMetricsCollector()
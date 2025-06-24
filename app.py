from prometheus_client import start_http_server, Gauge
import psutil
import mysql.connector
import time
import socket
import os
from dotenv import load_dotenv  

# Load environment variables from .env file
load_dotenv()

# Initialize metrics
CPU_USAGE = Gauge('host_cpu_usage', 'CPU usage %', ['hostname'])
DISK_TOTAL = Gauge('host_disk_total', 'Total disk space (bytes)', ['hostname', 'mount'])
DISK_USED = Gauge('host_disk_used', 'Used disk space (bytes)', ['hostname', 'mount'])
DISK_FREE = Gauge('host_disk_free', 'Free disk space (bytes)', ['hostname', 'mount'])
MYSQL_CONNECTIONS = Gauge('host_mysql_connections', 'Active connections', ['hostname'])
MYSQL_QUERIES = Gauge('host_mysql_queries', 'Queries per second', ['hostname'])
PROCESSED_VIDEOS = Gauge('processed_videos_count', 'Number of processed videos per site', ['site_id'])

def get_hostname():
    return os.getenv('HOSTNAME', socket.gethostname())

def get_disk_usage():
    """Cross-platform disk usage collection"""
    hostname = get_hostname()
    try:
        for partition in psutil.disk_partitions(all=True):
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                DISK_TOTAL.labels(hostname, partition.mountpoint).set(usage.total)
                DISK_USED.labels(hostname, partition.mountpoint).set(usage.used)
                DISK_FREE.labels(hostname, partition.mountpoint).set(usage.free)
            except Exception as e:
                print(f"Error reading {partition.mountpoint}: {str(e)}")
    except Exception as e:
        print(f"Disk monitoring error: {str(e)}")

def get_processed_videos():
    """Fetch and expose processed video counts per site"""
    try:
        conn = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST'),
            user=os.getenv('MYSQL_USER'),
            password=os.getenv('MYSQL_PASSWORD'),
            database=os.getenv('MYSQL_DB'),
            port=os.getenv('MYSQL_PORT', '3306'),
            connect_timeout=3
        )
        cursor = conn.cursor(dictionary=True)
        
        # Get processed videos count per site
        query = """
        SELECT 
            site_id, 
            COUNT(*) as processed_count
        FROM tbl_videos
        WHERE progress_value = 100 
          AND is_processed = 1
        GROUP BY site_id
        """
        cursor.execute(query)
        
        # Reset all metrics before updating
        PROCESSED_VIDEOS.clear()
        
        # Update metrics for each site
        for row in cursor:
            PROCESSED_VIDEOS.labels(site_id=str(row['site_id'])).set(row['processed_count'])
        
        cursor.close()
        conn.close()
    except mysql.connector.Error as e:
        print(f"MySQL connection error: {str(e)}")
    except Exception as e:
        print(f"Processed videos monitoring error: {str(e)}")

def get_mysql_metrics():
    hostname = get_hostname()
    try:
        conn = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST'),
            user=os.getenv('MYSQL_USER'),
            password=os.getenv('MYSQL_PASSWORD'),
            database=os.getenv('MYSQL_DB'),
            port=os.getenv('MYSQL_PORT', '3306'),
            connect_timeout=3
        )
        cursor = conn.cursor()
        
        cursor.execute("SHOW STATUS LIKE 'Threads_connected'")
        connections = int(cursor.fetchone()[1])
        
        cursor.execute("SHOW STATUS LIKE 'Queries'")
        queries = int(cursor.fetchone()[1])
        
        MYSQL_CONNECTIONS.labels(hostname).set(connections)
        MYSQL_QUERIES.labels(hostname).set(queries)
        
        cursor.close()
        conn.close()
    except mysql.connector.Error as e:
        print(f"MySQL connection error: {str(e)}")
    except Exception as e:
        print(f"MySQL monitoring error: {str(e)}")

if __name__ == '__main__':
    hostname = get_hostname()
    print(f"Starting exporter on port 8118 (Host: {hostname})")
    start_http_server(8118)
    
    while True:
        try:
            CPU_USAGE.labels(hostname).set(psutil.cpu_percent())
            get_disk_usage()
            get_mysql_metrics()
            get_processed_videos()
        except Exception as e:
            print(f"Monitoring error: {str(e)}")
        
        time.sleep(15)  # Reduced frequency to avoid DB overload
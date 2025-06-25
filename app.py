from prometheus_client import start_http_server, Gauge
import psutil
import mysql.connector
import time
import socket
import os
from dotenv import load_dotenv
import platform
import subprocess

# Load environment variables from .env file
load_dotenv()

# Initialize metrics
CPU_USAGE = Gauge('host_cpu_usage', 'CPU usage %', ['hostname'])
DISK_TOTAL = Gauge('host_disk_total', 'Total disk space (bytes)', ['hostname', 'mount'])
DISK_USED = Gauge('host_disk_used', 'Used disk space (bytes)', ['hostname', 'mount'])
DISK_FREE = Gauge('host_disk_free', 'Free disk space (bytes)', ['hostname', 'mount'])
MYSQL_CONNECTIONS = Gauge('host_mysql_connections', 'Active connections', ['hostname'])
MYSQL_QUERIES = Gauge('host_mysql_queries', 'Queries per second', ['hostname'])
PROCESSED_VIDEOS = Gauge('processed_videos_count', 'Number of processed videos', ['hostname'])

def get_hostname():
    # Try to get hostname from host filesystem first
    try:
        if os.path.exists('/host/etc/hostname'):
            with open('/host/etc/hostname') as f:
                return f.read().strip()
    except Exception:
        pass
    
    # Try environment variable or system hostname
    return os.getenv("HOSTNAME") or socket.gethostname()

def get_mysql_host():
    # Use localhost since we're using host networking
    return os.getenv("MYSQL_HOST", "localhost")

def get_disk_usage():
    hostname = get_hostname()
    rootfs = os.getenv('ROOTFS', '/')
    
    # Get actual mount points from host
    try:
        if os.path.exists('/host/proc/mounts'):
            with open('/host/proc/mounts', 'r') as f:
                mounts = set()
                for line in f:
                    parts = line.split()
                    if len(parts) >= 2 and parts[1].startswith('/'):
                        mount_point = parts[1]
                        if mount_point in ['/', '/home', '/var', '/boot', '/tmp']:
                            mounts.add(mount_point)
                
                for mount in mounts:
                    try:
                        host_path = os.path.join(rootfs, mount.lstrip('/'))
                        if os.path.exists(host_path):
                            usage = psutil.disk_usage(host_path)
                            DISK_TOTAL.labels(hostname, mount).set(usage.total)
                            DISK_USED.labels(hostname, mount).set(usage.used)
                            DISK_FREE.labels(hostname, mount).set(usage.free)
                    except Exception as e:
                        print(f"Error reading disk usage for {mount}: {e}")
        else:
            # Fallback to root filesystem
            usage = psutil.disk_usage(rootfs)
            DISK_TOTAL.labels(hostname, '/').set(usage.total)
            DISK_USED.labels(hostname, '/').set(usage.used)
            DISK_FREE.labels(hostname, '/').set(usage.free)
    except Exception as e:
        print(f"Error getting disk usage: {e}")

def get_processed_videos():
    hostname = get_hostname()
    try:
        conn = mysql.connector.connect(
            host=get_mysql_host(),
            user=os.getenv('MYSQL_USER'),
            password=os.getenv('MYSQL_PASSWORD'),
            database=os.getenv('MYSQL_DB'),
            port=int(os.getenv('MYSQL_PORT', '3306')),
            connect_timeout=3
        )
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT COUNT(*) as processed_count
            FROM video_uploads
            WHERE progress_value = 100 AND is_processed = 1
        """)
        row = cursor.fetchone()
        processed_count = row['processed_count'] if row and 'processed_count' in row else 0

        print(f"[INFO] Processed video count: {processed_count}")
        PROCESSED_VIDEOS.clear()
        PROCESSED_VIDEOS.labels(hostname).set(processed_count)

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
            host=get_mysql_host(),
            user=os.getenv('MYSQL_USER'),
            password=os.getenv('MYSQL_PASSWORD'),
            database=os.getenv('MYSQL_DB'),
            port=int(os.getenv('MYSQL_PORT', '3306')),
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
            # Get CPU usage with interval for accuracy
            cpu_percent = psutil.cpu_percent(interval=1)
            CPU_USAGE.labels(hostname).set(cpu_percent)
            get_disk_usage()
            get_mysql_metrics()
            get_processed_videos()
            print(f"[INFO] Metrics updated - CPU: {cpu_percent}%")
        except Exception as e:
            print(f"Monitoring error: {str(e)}")
        time.sleep(15)

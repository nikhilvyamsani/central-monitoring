from prometheus_client import start_http_server, Gauge
import psutil
import subprocess
import mysql.connector
import time
import socket
import platform

# Initialize metrics
CPU_USAGE = Gauge('host_cpu_usage', 'CPU usage %', ['hostname'])
DISK_TOTAL = Gauge('host_disk_total', 'Total disk space (bytes)', ['hostname', 'mount'])
DISK_USED = Gauge('host_disk_used', 'Used disk space (bytes)', ['hostname', 'mount'])
MYSQL_CONNECTIONS = Gauge('host_mysql_connections', 'Active connections', ['hostname'])
MYSQL_QUERIES = Gauge('host_mysql_queries', 'Queries per second', ['hostname'])

def get_hostname():
    return socket.gethostname()

def get_disk_usage():
    """Cross-platform disk usage collection"""
    try:
        # Use psutil for cross-platform compatibility
        for partition in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                DISK_TOTAL.labels(get_hostname(), partition.mountpoint).set(usage.total)
                DISK_USED.labels(get_hostname(), partition.mountpoint).set(usage.used)
            except Exception as e:
                print(f"Error reading {partition.mountpoint}: {str(e)}")
    except Exception as e:
        print(f"Disk monitoring error: {str(e)}")

def get_mysql_metrics():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="password",
            database="take-leap",
            port = 3306,
            connect_timeout=3
        )
        cursor = conn.cursor()
        
        # Get connections
        cursor.execute("SHOW STATUS LIKE 'Threads_connected'")
        connections = int(cursor.fetchone()[1])
        
        # Get queries
        cursor.execute("SHOW STATUS LIKE 'Queries'")
        queries = int(cursor.fetchone()[1])
        
        MYSQL_CONNECTIONS.labels(get_hostname()).set(connections)
        MYSQL_QUERIES.labels(get_hostname()).set(queries)
        
        cursor.close()
        conn.close()
    except mysql.connector.Error as e:
        print(f"MySQL connection error: {str(e)}")
    except Exception as e:
        print(f"MySQL monitoring error: {str(e)}")

if __name__ == '__main__':
    print(f"Starting exporter on port 8118 (Host: {get_hostname()})")
    start_http_server(8118)
    while True:
        try:
            CPU_USAGE.labels(get_hostname()).set(psutil.cpu_percent())
            get_disk_usage()
            get_mysql_metrics()
        except Exception as e:
            print(f"Monitoring error: {str(e)}")
        
        time.sleep(5)
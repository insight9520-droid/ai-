import os
import time
import platform
import subprocess
import requests
import socket
import psutil

class SecurityEngine:
    def __init__(self):
        self.log_file = "security_incident_report.txt"
        self.blocked_ips = []
        self.local_ip = self.get_local_ip()
        
    def get_local_ip(self):
        """현재 컴퓨터의 로컬 IP 확인"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    def monitor_network_connections(self):
        """현재 활성화된 네트워크 연결 감시 (외부 접근 탐지)"""
        try:
            connections = psutil.net_connections(kind='inet')
            external_access = []
            
            for conn in connections:
                if conn.status == 'ESTABLISHED' and conn.remote_address:
                    remote_ip = conn.remote_address.ip
                    # 로컬 호스트나 자신의 IP가 아닌 경우 외부 접근으로 간주
                    if remote_ip != '127.0.0.1' and remote_ip != self.local_ip:
                        external_access.append(remote_ip)
            
            return list(set(external_access))
        except:
            return []

    def block_ip(self, ip_address):
        """특정 IP를 윈도우 방화벽에서 즉시 차단"""
        if platform.system() == "Windows":
            try:
                cmd = f'netsh advfirewall firewall add rule name="BLOCK_INTRUDER_{ip_address}" dir=in action=block remoteip={ip_address}'
                subprocess.run(cmd, shell=True, check=True, capture_output=True)
                if ip_address not in self.blocked_ips:
                    self.blocked_ips.append(ip_address)
                self.log_incident(f"IP 차단 성공: {ip_address}")
                return True
            except Exception as e:
                self.log_incident(f"IP 차단 실패: {ip_address}, 에러: {str(e)}")
                return False
        return False

    def trace_ip(self, ip_address):
        """IP 위치 및 정보 추적"""
        try:
            res = requests.get(f"http://ip-api.com/json/{ip_address}", timeout=5)
            if res.status_code == 200:
                return res.json()
        except:
            pass
        return {"status": "fail", "message": "추적 불가"}

    def log_incident(self, message):
        """보안 사고 로그 기록"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")

    def check_dangerous_query(self, query):
        """위험한 쿼리/명령어 감지"""
        dangerous_keywords = ["DROP", "DELETE", "TRUNCATE", "FORMAT", "rm -rf", "shutdown", "SELECT * FROM users"]
        for keyword in dangerous_keywords:
            if keyword.upper() in query.upper():
                return True
        return False

    def get_system_health(self):
        """시스템 이상 징후 감시 (CPU 사용량 등)"""
        cpu_usage = psutil.cpu_percent(interval=0.1)
        ram_usage = psutil.virtual_memory().percent
        return {"cpu": cpu_usage, "ram": ram_usage, "alert": cpu_usage > 90}

# 싱글톤 인스턴스
security_monitor = SecurityEngine()

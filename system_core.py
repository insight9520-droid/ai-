import psutil
import ctypes
import sys
import os
import shutil
import platform
import socket
import subprocess
import json
import re
import requests
import random
from config import TAVILY_KEYS

# =========================
# 함수 레지스트리 (Function Registry)
# =========================
registry = {}

def register_action(name):
    def decorator(func):
        registry[name] = func
        return func
    return decorator

# =========================
# 관리자 권한
# =========================
def is_admin():
    try:
        if platform.system() == "Windows":
            return ctypes.windll.shell32.IsUserAnAdmin()
        return os.getuid() == 0
    except:
        return False

@register_action("request_admin")
def request_admin(*args, **kwargs):
    if not is_admin():
        if platform.system() == "Windows":
            params = " ".join([f'"{arg}"' for arg in sys.argv])
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, params, None, 1
            )
            sys.exit()
        else:
            return "Linux/Mac에서는 sudo를 사용해 주세요."
    return "이미 관리자 권한입니다."

# =========================
# 파일 시스템 관련
# =========================
@register_action("list_directory")
def list_directory(path=".", *args, **kwargs):
    # AI가 첫 번째 인자로 path를 주거나, keyword argument로 줄 수 있음
    target_path = args[0] if args else kwargs.get('path', path)
    target_path = os.path.abspath(target_path)
    
    if not os.path.exists(target_path): return f"Error: {target_path} 존재하지 않음"
    
    entries = []
    try:
        for name in sorted(os.listdir(target_path)):
            full_path = os.path.join(target_path, name)
            entries.append({
                "name": name,
                "is_dir": os.path.isdir(full_path),
                "size": os.path.getsize(full_path) if os.path.isfile(full_path) else None
            })
        return entries
    except Exception as e:
        return f"Error: {str(e)}"

@register_action("read_file")
def read_file(path=None, *args, **kwargs):
    target_path = args[0] if args else kwargs.get('path', path)
    if not target_path: return "Error: 파일 경로가 지정되지 않았습니다."
    
    target_path = os.path.abspath(target_path)
    if not os.path.isfile(target_path): return f"Error: {target_path} 파일이 아님"
    
    with open(target_path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()

@register_action("write_file")
def write_file(path=None, content="", mode="w", *args, **kwargs):
    # AI가 보낼 수 있는 다양한 키워드 대응 (content, contents, data 등)
    target_path = args[0] if args else kwargs.get('path', path)
    actual_content = kwargs.get('content', kwargs.get('contents', kwargs.get('data', content)))
    
    if not target_path: return "Error: 파일 경로가 지정되지 않았습니다."
    
    target_path = os.path.abspath(target_path)
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    with open(target_path, mode, encoding="utf-8", errors="replace") as f:
        f.write(actual_content)
    return f"Successfully written to {target_path}"

@register_action("delete_path")
def delete_path(path=None, *args, **kwargs):
    target_path = args[0] if args else kwargs.get('path', path)
    if not target_path: return "Error: 경로가 지정되지 않았습니다."
    
    target_path = os.path.abspath(target_path)
    if not os.path.exists(target_path): return f"Error: {target_path} 존재하지 않음"
    
    if os.path.isdir(target_path):
        shutil.rmtree(target_path)
    else:
        os.remove(target_path)
    return f"Successfully deleted {target_path}"

@register_action("search_files")
def search_files(keyword=None, path=".", limit=20, *args, **kwargs):
    target_keyword = args[0] if args else kwargs.get('keyword', keyword)
    target_path = kwargs.get('path', path)
    
    matches = []
    try:
        for root, dirs, files in os.walk(os.path.abspath(target_path)):
            for name in files:
                if not target_keyword or target_keyword.lower() in name.lower():
                    full_path = os.path.join(root, name)
                    try:
                        size = os.path.getsize(full_path)
                        matches.append({"path": full_path, "size": size})
                    except: continue
            if len(matches) > 500: break

        matches.sort(key=lambda x: x['size'], reverse=True)
        result = [f"{m['path']} ({round(m['size']/(1024*1024), 2)} MB)" for m in matches[:limit]]
        return result if result else "일치하는 파일을 찾지 못했습니다."
    except Exception as e:
        return f"검색 중 오류 발생: {str(e)}"

@register_action("search_web")
def search_web(query=None, *args, **kwargs):
    target_query = args[0] if args else kwargs.get('query', query)
    if not target_query: return "Error: 검색어가 없습니다."
    if not TAVILY_KEYS: return "Error: Tavily API 키가 없습니다."
    
    key = random.choice(TAVILY_KEYS)
    try:
        res = requests.post(
            "https://api.tavily.com/search",
            json={"api_key": key, "query": target_query, "max_results": 3},
            timeout=10
        )
        if res.status_code == 200:
            results = res.json().get("results", [])
            return "\n\n".join([f"제목: {r['title']}\n내용: {r['content']}\n링크: {r['url']}" for r in results])
        return f"Error: Tavily API 오류 ({res.status_code})"
    except Exception as e:
        return f"Error: 웹 검색 오류 ({str(e)})"

# =========================
# 시스템 정보 관련 (인자 무시 기능 추가)
# =========================
@register_action("sys.status")
def get_status(*args, **kwargs):
    return {
        "cpu": psutil.cpu_percent(interval=0.1),
        "ram": psutil.virtual_memory().percent
    }

@register_action("sys.drives")
def get_drives(*args, **kwargs):
    return [p._asdict() for p in psutil.disk_partitions(all=True)]

@register_action("sys.disk_usage")
def get_disk_usage(path=".", *args, **kwargs):
    target_path = args[0] if args else kwargs.get('path', path)
    usage = shutil.disk_usage(os.path.abspath(target_path))
    return {
        "total": usage.total,
        "used": usage.used,
        "free": usage.free,
        "percent": round((usage.used / usage.total) * 100, 2)
    }

@register_action("get_os_info")
def get_os_info(*args, **kwargs):
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "python": platform.python_version()
    }

@register_action("get_gpu_info")
def get_gpu_info(*args, **kwargs):
    if platform.system() == "Windows":
        try:
            # PowerShell을 사용하여 더 상세하고 확실하게 GPU 정보를 가져옵니다.
            cmd = "powershell -Command \"Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name\""
            output = subprocess.check_output(cmd, shell=True, text=True)
            gpus = [l.strip() for l in output.splitlines() if l.strip()]
            return gpus if gpus else ["GPU 정보를 찾을 수 없습니다."]
        except Exception as e:
            return [f"GPU 정보 조회 실패 (PowerShell): {str(e)}"]
    return ["Linux/Mac GPU 조회는 추가 구현 필요"]

@register_action("get_network_info")
def get_network_info(*args, **kwargs):
    return {name: [a._asdict() for a in addrs] for name, addrs in psutil.net_if_addrs().items()}

@register_action("get_processes")
def get_processes(limit=10, *args, **kwargs):
    target_limit = args[0] if args else kwargs.get('limit', limit)
    procs = []
    for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try: procs.append(p.info)
        except: continue
    return sorted(procs, key=lambda x: x['cpu_percent'] or 0, reverse=True)[:int(target_limit)]

@register_action("kill_process")
def kill_process(name_or_pid=None, *args, **kwargs):
    target = args[0] if args else kwargs.get('name_or_pid', name_or_pid)
    if not target: return "Error: 프로세스 명이나 PID가 없습니다."
    
    for p in psutil.process_iter(['pid', 'name']):
        try:
            if str(p.info['pid']) == str(target) or p.info['name'].lower() == str(target).lower():
                p.terminate()
                return f"Process {target} terminated."
        except: continue
    return f"Process {target} not found."

@register_action("get_service_status")
def get_service_status(service_name=None, *args, **kwargs):
    target = args[0] if args else kwargs.get('service_name', service_name)
    if platform.system() == "Windows":
        cmd = f"Get-Service {target if target else ''} | Select-Object Name, Status | ConvertTo-Json"
        try:
            output = subprocess.check_output(["powershell", "-Command", cmd], text=True)
            return json.loads(output)
        except: return "서비스 정보 조회 실패"
    return "Linux 서비스 조회는 추가 구현 필요"

# =========================
# 보안 엔진 (Security Engine)
# =========================
@register_action("sec.block_ip")
def block_ip(ip_address, *args, **kwargs):
    """특정 IP를 윈도우 방화벽에서 차단"""
    if platform.system() == "Windows":
        try:
            cmd = f'netsh advfirewall firewall add rule name="BLOCK_INTRUDER_{ip_address}" dir=in action=block remoteip={ip_address}'
            subprocess.run(cmd, shell=True, check=True)
            return f"IP {ip_address}가 성공적으로 차단되었습니다."
        except Exception as e:
            return f"IP 차단 실패 (관리자 권한 필요): {str(e)}"
    return "Linux/Mac에서는 iptables/ufw를 사용해야 합니다."

@register_action("sec.trace_ip")
def trace_ip(ip_address, *args, **kwargs):
    """IP 위치 및 정보 추적 (외부 API 활용)"""
    try:
        res = requests.get(f"http://ip-api.com/json/{ip_address}", timeout=5)
        if res.status_code == 200:
            data = res.json()
            return {
                "ip": ip_address,
                "country": data.get("country"),
                "city": data.get("city"),
                "isp": data.get("isp"),
                "lat": data.get("lat"),
                "lon": data.get("lon")
            }
        return f"IP 추적 실패: {res.status_code}"
    except Exception as e:
        return f"IP 추적 중 오류: {str(e)}"

@register_action("sec.log_incident")
def log_incident(incident_data, *args, **kwargs):
    """보안 사고 리포트 생성"""
    log_path = os.path.join(os.getcwd(), "security_incident_report.txt")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"\n[{platform.node()}] 보안 사고 발생 리포트\n")
        f.write(f"시간: {kwargs.get('time', 'N/A')}\n")
        f.write(f"내용: {incident_data}\n")
        f.write("-" * 50 + "\n")
    return f"사고 리포트가 저장되었습니다: {log_path}"

# =========================
# 실행기 (Dispatcher)
# =========================
def execute_action(action_name, target=None, params=None):
    if action_name not in registry:
        return f"Error: Action '{action_name}' is not registered."
    
    func = registry[action_name]
    params = params or {}
    
    try:
        # AI가 target을 줬으면 첫 번째 인자로, params는 키워드 인자로 전달
        if target:
            return func(target, **params)
        return func(**params)
    except Exception as e:
        return f"Execution Error: {str(e)}"

def get_registered_actions():
    return list(registry.keys())

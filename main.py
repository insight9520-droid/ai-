import sys
import json
import threading
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTextEdit, QPushButton, QLabel, QMessageBox, QDialog)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QColor
from ai_module import handle_with_feedback
from system_core import execute_action
from security_engine import security_monitor

class SecurityAlertDialog(QDialog):
    """보안 경고 팝업 (최상단 강제 표시)"""
    def __init__(self, title, message, alert_type="warning"):
        super().__init__()
        self.setWindowTitle(title)
        self.setGeometry(200, 200, 700, 400)
        
        if alert_type == "critical":
            bg_color = "#2a0a0a"
            border_color = "#ff0000"
            text_color = "#ff4444"
        elif alert_type == "lockdown":
            bg_color = "#0a0a2a"
            border_color = "#0066ff"
            text_color = "#00ccff"
        else:
            bg_color = "#1a1a0a"
            border_color = "#ffaa00"
            text_color = "#ffaa00"
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {bg_color};
                border: 4px solid {border_color};
            }}
            QLabel {{
                color: #ffffff;
                font-size: 14px;
            }}
            QPushButton {{
                background-color: {border_color};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {text_color};
            }}
        """)
        
        layout = QVBoxLayout()
        
        # 경고 메시지
        msg_label = QLabel(message)
        msg_label.setStyleSheet(f"color: {text_color}; font-size: 16px; font-weight: bold;")
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)
        
        # 확인 버튼
        ok_btn = QPushButton("확인")
        ok_btn.clicked.connect(self.accept)
        layout.addWidget(ok_btn)
        
        self.setLayout(layout)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        self.exec()

class AIWorker(QThread):
    response_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    
    def __init__(self, user_input):
        super().__init__()
        self.user_input = user_input
    
    def run(self):
        try:
            result = handle_with_feedback(self.user_input)
            if result:
                if isinstance(result, dict) and "action" in result:
                    action = result.get("action", "none")
                    target = result.get("target")
                    params = result.get("params", {})
                    response = result.get("response", "작업 완료")
                    
                    # 액션 실행
                    if action != "none":
                        exec_result = execute_action(action, target, params)
                        response += f"\n\n[결과]: {exec_result}"
                    
                    self.response_signal.emit(response)
                else:
                    self.response_signal.emit(str(result))
            else:
                self.error_signal.emit("응답을 받지 못했습니다.")
        except Exception as e:
            self.error_signal.emit(f"오류 발생: {str(e)}")

class ModernChatUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI OS 에이전트")
        self.setGeometry(100, 100, 900, 700)
        self.setStyleSheet(self.get_stylesheet())
        self.init_ui()
        self.worker = None
        self.security_mode = False
        self.intrusion_attempts = 0
        self.security_thread = None
        self.start_security_monitoring()
    
    def get_stylesheet(self):
        return """
        QMainWindow {
            background-color: #0d1117;
        }
        
        QWidget {
            background-color: #0d1117;
            color: #e6edf3;
        }
        
        QTextEdit {
            background-color: #161b22;
            color: #e6edf3;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 12px;
            font-size: 14px;
            font-family: 'Segoe UI', Arial;
        }
        
        QTextEdit:focus {
            border: 2px solid #58a6ff;
            background-color: #0d1117;
        }
        
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                       stop:0 #1f6feb, stop:1 #388bfd);
            color: white;
            border: none;
            border-radius: 6px;
            padding: 10px 20px;
            font-weight: bold;
            font-size: 13px;
            font-family: 'Segoe UI', Arial;
        }
        
        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                       stop:0 #388bfd, stop:1 #58a6ff);
        }
        
        QPushButton:pressed {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                       stop:0 #0969da, stop:1 #1f6feb);
        }
        
        QLabel {
            color: #8b949e;
            font-size: 12px;
            font-family: 'Segoe UI', Arial;
        }
        """
    
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 제목
        title = QLabel("🤖 AI OS 에이전트 (보안 모드 활성화)")
        title_font = QFont("Segoe UI", 18, QFont.Weight.Bold)
        title.setFont(title_font)
        title.setStyleSheet("color: #58a6ff; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # 상태 표시
        self.status_label = QLabel("준비 완료 ✓ | 보안 모니터링 활성화")
        self.status_label.setStyleSheet("color: #3fb950; font-size: 12px;")
        layout.addWidget(self.status_label)
        
        # 채팅 표시 영역
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setMinimumHeight(400)
        self.chat_display.setStyleSheet("""
            QTextEdit {
                background-color: #010409;
                color: #e6edf3;
                border: 2px solid #30363d;
                border-radius: 10px;
                padding: 15px;
                font-size: 13px;
            }
        """)
        layout.addWidget(self.chat_display)
        
        # 입력 영역
        input_label = QLabel("명령 입력:")
        input_label.setStyleSheet("color: #8b949e; font-weight: bold;")
        layout.addWidget(input_label)
        
        self.input_field = QTextEdit()
        self.input_field.setMaximumHeight(80)
        self.input_field.setPlaceholderText("여기에 명령을 입력하세요...")
        layout.addWidget(self.input_field)
        
        # 버튼 영역
        button_layout = QHBoxLayout()
        
        send_btn = QPushButton("📤 전송 (Ctrl+Enter)")
        send_btn.clicked.connect(self.send_command)
        send_btn.setMinimumHeight(40)
        button_layout.addWidget(send_btn)
        
        security_btn = QPushButton("🛡️ 보안 테스트")
        security_btn.clicked.connect(self.test_security_alerts)
        security_btn.setMinimumHeight(40)
        security_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                           stop:0 #ff6b35, stop:1 #ff8c42);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                           stop:0 #ff8c42, stop:1 #ffa500);
            }
        """)
        button_layout.addWidget(security_btn)
        
        clear_btn = QPushButton("🗑️ 초기화")
        clear_btn.clicked.connect(self.clear_chat)
        clear_btn.setMinimumHeight(40)
        clear_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                           stop:0 #da3633, stop:1 #f85149);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                           stop:0 #f85149, stop:1 #ff7b72);
            }
        """)
        button_layout.addWidget(clear_btn)
        
        layout.addLayout(button_layout)
        
        # 키 바인딩
        self.input_field.keyPressEvent = self.handle_key_press
        
        # 초기 메시지
        self.add_message("🤖 AI", "안녕하세요! 저는 AI OS 에이전트입니다.\n\n🛡️ 보안 모드가 활성화되었습니다.\n- 비인가 접근 시도 감지 시 자동 경고\n- 위험한 명령 자동 차단\n- 침입자 IP 자동 추적 및 차단\n\n무엇을 도와드릴까요?")
    
    def handle_key_press(self, event):
        if event.key() == Qt.Key.Key_Return and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.send_command()
        else:
            QTextEdit.keyPressEvent(self.input_field, event)
    
    def send_command(self):
        user_input = self.input_field.toPlainText().strip()
        if not user_input:
            return
        
        self.add_message("👤 당신", user_input)
        self.input_field.clear()
        self.status_label.setText("🔄 처리 중...")
        self.status_label.setStyleSheet("color: #d29922;")
        
        self.worker = AIWorker(user_input)
        self.worker.response_signal.connect(self.on_response)
        self.worker.error_signal.connect(self.on_error)
        self.worker.start()
    
    def on_response(self, response):
        self.add_message("🤖 AI", response)
        self.status_label.setText("준비 완료 ✓")
        self.status_label.setStyleSheet("color: #3fb950;")
    
    def on_error(self, error):
        self.add_message("⚠️ 오류", error)
        self.status_label.setText("오류 발생 ✗")
        self.status_label.setStyleSheet("color: #f85149;")
    
    def add_message(self, sender, message):
        if sender == "👤 당신":
            formatted = f"<div style='background-color: #161b22; padding: 10px; border-radius: 8px; margin: 5px 0; border-left: 3px solid #58a6ff;'><b style='color: #58a6ff;'>{sender}</b><br><span style='color: #e6edf3;'>{message}</span></div>"
        elif sender == "🤖 AI":
            formatted = f"<div style='background-color: #0f3460; padding: 10px; border-radius: 8px; margin: 5px 0; border-left: 3px solid #3fb950;'><b style='color: #3fb950;'>{sender}</b><br><span style='color: #e6edf3;'>{message}</span></div>"
        elif sender == "🛡️ 보안":
            formatted = f"<div style='background-color: #1a2a1a; padding: 10px; border-radius: 8px; margin: 5px 0; border-left: 3px solid #00ff00;'><b style='color: #00ff00;'>{sender}</b><br><span style='color: #e6edf3;'>{message}</span></div>"
        else:
            formatted = f"<div style='background-color: #3d1f1f; padding: 10px; border-radius: 8px; margin: 5px 0; border-left: 3px solid #f85149;'><b style='color: #f85149;'>{sender}</b><br><span style='color: #ffcccc;'>{message}</span></div>"
        
        self.chat_display.append(formatted)
        self.chat_display.verticalScrollBar().setValue(
            self.chat_display.verticalScrollBar().maximum()
        )
    
    def clear_chat(self):
        self.chat_display.clear()
        self.add_message("🤖 AI", "채팅 기록이 초기화되었습니다.")
    
    def start_security_monitoring(self):
        """백그라운드에서 보안 모니터링 시작"""
        import threading
        self.security_thread = threading.Thread(target=self.security_monitor_loop, daemon=True)
        self.security_thread.start()
    
    def security_monitor_loop(self):
        """실시간 보안 모니터링 루프"""
        while True:
            try:
                # 외부 접근 감시
                external_ips = security_monitor.monitor_network_connections()
                for ip in external_ips:
                    if ip not in security_monitor.blocked_ips:
                        self.trigger_security_alert_level1(ip)
                        security_monitor.block_ip(ip)
                
                # 시스템 건강 체크
                health = security_monitor.get_system_health()
                if health["alert"]:
                    self.add_message("⚠️ 시스템", f"CPU 사용량 {health['cpu']}% - 비정상 높음!")
                
                time.sleep(2)  # 2초마다 체크
            except:
                time.sleep(5)
    
    def test_security_alerts(self):
        """보안 경고 테스트 (데모용)"""
        self.trigger_security_alert_level1("192.168.1.100")
        self.trigger_security_alert_level2("DROP TABLE users;")
        self.trigger_security_lockdown("192.168.1.100")
    
    def trigger_security_alert_level1(self, ip_address="Unknown"):
        """1차 경고: 비인가 접근 감지"""
        self.security_mode = True
        self.intrusion_attempts += 1
        
        alert_msg = f"""⚠️ 비인가 접근 시도 감지!

IP 주소: {ip_address}
시도 횟수: {self.intrusion_attempts}

당사는 불법적 접근시도를 감시하고 있습니다.
즉시 접근을 중단하시기 바랍니다."""
        
        SecurityAlertDialog("🚨 보안 경고 - 1차", alert_msg, "warning")
        self.add_message("🛡️ 보안", f"비인가 접근 감지: {ip_address}")
    
    def trigger_security_alert_level2(self, command="Unknown"):
        """2차 경고: 위험한 쿼리 실행 시도"""
        alert_msg = f"""🚨 위험한 명령 실행 시도 감지!

명령어: {command}

쿼리 실행 진행 확인.
당장 멈추시오!

이 행위는 기록되며 법적 조치를 받을 수 있습니다."""
        
        SecurityAlertDialog("🚨 보안 경고 - 2차", alert_msg, "critical")
        self.add_message("🛡️ 보안", f"위험한 명령 차단: {command}")
    
    def trigger_security_lockdown(self, ip_address="Unknown"):
        """3차 대응: 시스템 잠금 및 IP 차단"""
        lockdown_msg = f"""🔒 시스템 보안 잠금 활성화!

침입자 IP: {ip_address}
상태: IP 영구 차단됨

이 사건은 자동으로 기록되었습니다.
112에 신고 가능한 상태입니다.

보안 리포트: security_incident_report.txt"""
        
        SecurityAlertDialog("🔒 시스템 잠금", lockdown_msg, "lockdown")
        self.add_message("🛡️ 보안", f"시스템 잠금 활성화 - IP {ip_address} 차단됨")

def main():
    app = QApplication(sys.argv)
    window = ModernChatUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

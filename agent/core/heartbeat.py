import threading
import time

from agent.core.client import send_heartbeat

class Heartbeat:
    def __init__(self, on_result=None):
        self.running = False
        self.on_result = on_result

    def _send(self):
        try:
            response = send_heartbeat()
            if self.on_result:
                self.on_result(True, response.status_code, None)
        except Exception as error:
            if self.on_result:
                self.on_result(False, None, str(error))

    def start(self):
        self.running = True
        def loop():
            while self.running:
                self._send()
                from agent.core.config import get_config
                time.sleep(get_config().get('heartbeat_interval', 30))
        threading.Thread(target=loop, daemon=True).start()

    def stop(self):
        self.running = False

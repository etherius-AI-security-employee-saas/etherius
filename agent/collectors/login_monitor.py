import threading, time, queue, platform
from datetime import datetime

class LoginMonitor:
    def __init__(self, q: queue.Queue):
        self.q = q; self.running = False

    def _collect(self):
        self.q.put({"event_type":"session_heartbeat","severity":"info","payload":{
            "session_type":"active","hour_of_day":datetime.now().hour,
            "failed_attempts":0,"is_remote":False,"platform":platform.system()
        }})

    def start(self):
        self.running = True
        def loop():
            while self.running:
                self._collect(); time.sleep(300)
        threading.Thread(target=loop, daemon=True).start()

    def stop(self): self.running = False

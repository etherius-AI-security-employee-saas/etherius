import threading, time, queue, platform

class ProcessMonitor:
    def __init__(self, q: queue.Queue):
        self.q = q; self.running = False; self._seen = set()

    def _collect(self):
        try:
            import psutil
            current = set()
            for p in psutil.process_iter(['pid','name','cmdline','username']):
                try:
                    i = p.info; pid = i['pid']; current.add(pid)
                    if pid not in self._seen:
                        self.q.put({"event_type":"process","severity":"info","payload":{
                            "pid":pid,"process_name":i.get('name',''),
                            "cmd_line":' '.join(i.get('cmdline',[]) or []),
                            "username":i.get('username',''),"elevated":False,"platform":platform.system()
                        }})
                except: pass
            self._seen = current
        except ImportError: pass

    def start(self):
        self.running = True
        def loop():
            while self.running:
                self._collect(); time.sleep(10)
        threading.Thread(target=loop, daemon=True).start()

    def stop(self): self.running = False

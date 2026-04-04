import threading, time, queue, os, platform

WATCH = {"Windows":["C:\\Users","C:\\Windows\\Temp"],"Linux":["/etc","/tmp"]}.get(platform.system(),["/tmp"])

class FileMonitor:
    def __init__(self, q: queue.Queue):
        self.q = q; self.running = False; self._snap = {}

    def _scan(self, d):
        s = {}
        try:
            for f in os.listdir(d):
                p = os.path.join(d, f)
                try: s[p] = os.stat(p).st_mtime
                except: pass
        except: pass
        return s

    def _collect(self):
        for d in WATCH:
            cur = self._scan(d); prev = self._snap.get(d, {})
            changed = [p for p, m in cur.items() if prev.get(p) != m and p in prev]
            created = [p for p in cur if p not in prev]
            if changed or created:
                self.q.put({"event_type":"file","severity":"info","payload":{
                    "directory":d,"action":"modify",
                    "files_affected":len(changed)+len(created),
                    "file_path":(changed+created)[0] if changed or created else "",
                    "platform":platform.system()
                }})
            self._snap[d] = cur

    def start(self):
        self.running = True
        def loop():
            while self.running:
                self._collect(); time.sleep(60)
        threading.Thread(target=loop, daemon=True).start()

    def stop(self): self.running = False

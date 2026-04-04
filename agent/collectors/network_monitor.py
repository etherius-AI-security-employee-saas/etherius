import threading, time, queue

class NetworkMonitor:
    def __init__(self, q: queue.Queue):
        self.q = q; self.running = False; self._seen = set()

    def _collect(self):
        try:
            import psutil
            for c in psutil.net_connections(kind='inet'):
                if c.status == 'ESTABLISHED' and c.raddr:
                    key = (c.laddr.port, c.raddr.ip, c.raddr.port)
                    if key not in self._seen:
                        self._seen.add(key)
                        io = psutil.net_io_counters()
                        self.q.put({"event_type":"network","severity":"info","payload":{
                            "local_port":c.laddr.port,"dest_ip":c.raddr.ip,"dest_port":c.raddr.port,
                            "status":c.status,"bytes_sent":io.bytes_sent,"bytes_recv":io.bytes_recv,
                            "connection_count":len(list(psutil.net_connections()))
                        }})
        except ImportError: pass

    def start(self):
        self.running = True
        def loop():
            while self.running:
                self._collect(); time.sleep(15)
        threading.Thread(target=loop, daemon=True).start()

    def stop(self): self.running = False

import time

import httpx


class Api:
    def __init__(self, base_url: str, retries: int = 6):
        self.c = httpx.Client(base_url=base_url, timeout=120)
        self.retries = retries

    def request(self, method: str, path: str, **kw) -> tuple[int, object]:
        delay = 0.5
        for attempt in range(self.retries + 1):
            try:
                r = self.c.request(method, path, **kw)
            except httpx.TransportError:
                if attempt == self.retries:
                    raise
                time.sleep(delay)
                delay = min(delay * 2, 10)
                continue
            if r.status_code >= 500 and attempt < self.retries:
                time.sleep(delay)
                delay = min(delay * 2, 10)
                continue
            try:
                body = r.json()
            except ValueError:
                body = r.text
            return r.status_code, body
        raise RuntimeError("unreachable")

    def get(self, path, **kw):
        return self.request("GET", path, **kw)

    def post(self, path, json=None):
        return self.request("POST", path, json=json)

    def put(self, path, json=None):
        return self.request("PUT", path, json=json)

    def chunk_lines(self, n: int):
        with self.c.stream("GET", f"/events/chunks/{n}") as r:
            r.raise_for_status()
            for line in r.iter_lines():
                yield line

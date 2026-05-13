import httpx


def fetch_text(url: str, timeout: float = 20.0) -> str:
    with httpx.Client(timeout=timeout, follow_redirects=True, headers={"User-Agent": "LeadFind/0.1"}) as client:
        response = client.get(url)
        response.raise_for_status()
        return response.text

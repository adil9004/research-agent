def web_search(query: str) -> list:
    """Search DuckDuckGo for a query and return top 5 results."""
    try:
        # Import inside the function to avoid ImportError at module import time
        from ddgs import DDGS
        # Use DDGS as a context manager which ensures proper cleanup
        with DDGS() as ddgs:
            # ``text`` returns a list of dictionaries with at least the keys
            # ``title``, ``href`` and ``body``. Limit to the first 5 results.
            raw_results = ddgs.text(query, max_results=5)
        # Transform raw results to the required format
        formatted = []
        for r in raw_results:
            # Some keys might be missing, use ``dict.get`` with a fallback
            title = r.get("title")
            url = r.get("href")
            snippet = r.get("body")
            formatted.append({"title": title, "url": url, "snippet": snippet})
        return formatted
    except Exception:
        # In case of any error (e.g., missing package, network issue) return empty list
        return []


def fetch_page(url: str) -> str:
    """Fetch visible text from a URL, trimmed to first 3000 characters."""
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError as e:
        return f"Error: Missing required package - {e}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes
        soup = BeautifulSoup(response.text, 'html.parser')
        # Get visible text
        text = soup.get_text()
        # Clean up whitespace: split and rejoin to remove excessive whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        # Trim to first 3000 characters
        if len(text) > 3000:
            text = text[:3000]
        return text
    except Exception as e:
        return f"Error: {e}"

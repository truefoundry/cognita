import requests

from backend.settings import settings


def intent_summary_search(query: str):
    url = f"https://api.search.brave.com/res/v1/web/search?q={query}&summary=1"

    payload = {}
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": f"{settings.BRAVE_API_KEY}",
    }

    response = requests.request("GET", url, headers=headers, data=payload)
    answer = response.json()

    if "summarizer" in answer.keys():
        summary_query = answer["summarizer"]["key"]
        url = (
            f"https://api.search.brave.com/res/v1/summarizer/search?key={summary_query}"
        )
        response = requests.request("GET", url, headers=headers, data=payload)
        answer = response.json()["summary"][0]["data"]
        return answer
    return ""

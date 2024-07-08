import requests

from backend.settings import settings


def internet_search(query: str):
    headers = {
        "Accept": "     application/json",
        "X-Subscription-Token": f"{settings.BRAVE_API_KEY}",
    }

    params = {
        "q": f"{query}",
    }

    # response = requests.get('https://api.search.brave.com/res/v1/web/search', params=params, headers=headers)
    # response.raise_for_status()
    # answer = response.json()

    answer = "DEMO ANSWER FROM INTERNET SEARCH"
    return answer


def intent_summary_search(query: str):
    headers = {
        "Accept": "application/json",
        # 'Accept-Encoding': 'gzip',
        "X-Subscription-Token": f"{settings.BRAVE_API_KEY}",
    }

    params = {
        "q": f"{query}",
        "summary": "1",
    }

    # response = requests.get('https://api.search.brave.com/res/v1/web/search', params=params, headers=headers)
    # response.raise_for_status()
    # answer = response.json()

    answer = "DEMO ANSWER FROM INTENT SUMMARY SEARCH"
    return answer

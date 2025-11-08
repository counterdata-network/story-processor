import datetime as dt
import logging
from typing import Any, Dict, List, Optional

import requests
import requests.exceptions
from requests_ratelimiter import LimiterAdapter

from processor import NEWSCATCHER_API_KEY

# Setup a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def create_session(rate_limit: Optional[int] = 1) -> requests.Session:
    """
    Create a requests session with a rate limiter.

    Args:
        rate_limit (Optional[int]): The number of requests allowed per second where the default is 1.

    Returns:
        requests.Session: A configured requests session
    """
    session = requests.Session()
    limiter = LimiterAdapter(per_second=rate_limit)
    session.mount("https://", limiter)

    return session


def search_stories(
    q: str,
    language: str,
    countries: List[str],
    start_date: dt,
    end_date: dt,
    page: int = 1,
    page_size: int = 200,
    session: Optional[requests.Session] = None,
) -> Dict[str, Any]:
    """
    Fetch stories from the Newscatcher API based on provided parameters.

    Args:
        session (requests.Session): A requests session to use for the API call.
        q (str): Search terms for the query.
        language (str): desired language.
        countries (List[str]): desired countries
        start_date (datetime): the start date for the search.
        end_date (datetime): the end date for the search.
        page (int, optional): The page number to fetch where the default is 1.
        page_size (int, optional): The number of results per page where the default is 200.

    Returns:
        Dict[str, Any]: The JSON response containing the stories if successful.
    """
    params = {
        "q": q,
        "lang": language.lower(),
        "countries": countries,
        "page_size": page_size,
        "from_": start_date.strftime("%Y-%m-%d"),
        "to_": end_date.strftime("%Y-%m-%d"),
        "page": page,
    }

    # create session if one isn't passed
    if session is None:
        session = create_session()

    # fetch stories from newscatcher API, log errors
    try:
        response = session.get(
            "https://v3-api.newscatcherapi.com/api/search",
            headers={"x-api-token": NEWSCATCHER_API_KEY},
            params=params,
        )

        if response.status_code == 200:
            return response.json()
        else:
            logger.error(
                f"Failed to fetch stories. Status code: {response.status_code} - {response.reason}"
            )

    except requests.exceptions.RequestException as re:
        logger.error(f"Request exception occurred: {re}")

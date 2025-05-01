import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


def chunks(lst, n):
    """
    Yield successive n-sized chunks from lst.
    https://stackoverflow.com/questions/312443/how-do-you-split-a-list-into-evenly-sized-chunks
    """
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def remove_duplicate_by_title_media_id(stories: List[Dict]) -> List[Dict]:
    """
    Remove duplicate stories based on matching title and media_id. Keeps only one story for
    each unique combination.
    :param stories List of story dictionaries with 'title' and 'media_id' properties

    :return: List of stories that have any with duplicate title+media_id removed
    """
    seen = set()  # Set to track unique combinations
    unique_stories = []
    for story in stories:
        media_identifier = (
            story["media_id"] if "media_id" in story else story["media_name"]
        )
        identifier = str(media_identifier) + story["title"]
        # Only add to results if we haven't seen this combination before
        if identifier not in seen:
            seen.add(identifier)
            unique_stories.append(story)
    logger.debug(
        "  Removed {} duplicate stories based on title and media_id".format(
            len(stories) - len(unique_stories)
        )
    )
    return unique_stories

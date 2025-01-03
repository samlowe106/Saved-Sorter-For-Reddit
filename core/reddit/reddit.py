import asyncio
import itertools
import os
from datetime import timedelta
from enum import Enum
from typing import Iterable, List

import httpx
import praw
from praw.models import ListingGenerator, Redditor
from praw.models.subreddits import Subreddit

from .submission_wrapper import SubmissionWrapper


def sign_in(username: str = None, password: str = None) -> praw.Reddit:
    """
    Signs in to reddit

    :raises OAuthException:
    """
    if username and password:
        return praw.Reddit(
            client_id=os.environ.get("REDDIT_CLIENT_ID"),
            client_secret=os.environ.get("REDDIT_CLIENT_SECRET"),
            user_agent="PaperScraper",
            username=username,
            password=password,
        )
    return praw.Reddit(
        client_id=os.environ.get("REDDIT_CLIENT_ID"),
        client_secret=os.environ.get("REDDIT_CLIENT_SECRET"),
        user_agent="PaperScraper",
    )


class SortOption(Enum):
    """
    Represents the ways a subreddit's submissions can be sorted
    """

    def TOP_ALL(subreddit, **kwargs):
        return Subreddit.top(self=subreddit, time_filter="all", **kwargs)

    def TOP_DAY(subreddit, **kwargs):
        return Subreddit.top(self=subreddit, time_filter="day", **kwargs)

    def TOP_HOUR(subreddit, **kwargs):
        return Subreddit.top(self=subreddit, time_filter="hour", **kwargs)

    def TOP_WEEK(subreddit, **kwargs):
        return Subreddit.top(self=subreddit, time_filter="week", **kwargs)

    def TOP_MONTH(subreddit, **kwargs):
        return Subreddit.top(self=subreddit, time_filter="month", **kwargs)

    def TOP_YEAR(subreddit, **kwargs):
        return Subreddit.top(self=subreddit, time_filter="year", **kwargs)

    NEW = Subreddit.new
    HOT = Subreddit.hot
    CONTROVERSIAL = Subreddit.controversial
    GILDED = Subreddit.gilded

    def __call__(self, *args, **kwargs):
        self.value(*args, **kwargs)


async def _from_source(
    source: ListingGenerator,
    client: httpx.AsyncClient,
    amount: int = 10,
    dry: bool = True,
) -> List[SubmissionWrapper]:
    """
    Returns a list containing at most amount number of SubmissionWrappers,
    created from posts from the given source
    """
    if amount < 1:
        raise ValueError("Amount must be a positive integer")
    # basically, just get batches of 2 * amount and filter out the ones that don't have urls
    #  until we have enough. Worst case (for a single iteration) is that we only need 1
    #  additional post to reach the desired amount but try_amount is large
    try_amount = 2 * amount
    batch: List[SubmissionWrapper] = []
    exhausted = False
    while (not exhausted) and len(batch) < amount:
        prospective = [
            SubmissionWrapper(submission, client, dry=dry)
            for submission in itertools.islice(source, try_amount)
        ]
        # await all the urls
        await asyncio.gather(
            *(submission.find_urls(client) for submission in prospective)
        )
        if len(prospective) <= try_amount:
            # might have 0 < len(prospective) < try_amount
            exhausted = True

        def criteria(wrapped: SubmissionWrapper) -> bool:
            return len(wrapped.urls) > 0

        batch += list(filter(criteria, prospective))
    return batch[:amount]


async def from_saved(
    redditor: Redditor,
    client: httpx.AsyncClient,
    score: int = None,
    age: timedelta = None,
    amount: int = 10,
    dry: bool = True,
) -> List[SubmissionWrapper]:
    """Generates a batch of at most (amount) SubmissionWrappers from the given users' saved posts"""
    if amount < 1:
        raise ValueError("Amount must be a positive integer")
    return await _from_source(
        redditor.saved(limit=None, score=score, age=age), client, amount=amount, dry=dry
    )


async def from_subreddit(
    reddit: praw.Reddit,
    subreddit_name: str,
    sort_by: SortOption,
    client: httpx.AsyncClient,
    score: int = None,
    age: timedelta = None,
    amount: int = 10,
) -> Iterable[SubmissionWrapper]:
    """Generates a batch of at most (amount) SubmissionWrappers from the given subreddit"""
    if amount < 1:
        raise ValueError("Amount must be a positive integer")
    return await _from_source(
        sort_by(
            reddit.subreddit(subreddit_name.removeprefix("r/")), score=score, age=age
        ),
        client,
        amount=amount,
        dry=True,  # Can't/shouldn't unsave posts from subreddits
    )

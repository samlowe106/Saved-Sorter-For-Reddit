import asyncio
import json
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

import httpx
from praw.models import Submission

import core
from core import parsers


async def urls_responses(
    urls: str, client: httpx.AsyncClient
) -> Tuple[str, httpx.Response]:
    return asyncio.gather(*((url, await client.get(url, timeout=10)) for url in urls))


@dataclass
class SubmissionWrapper:
    """Wraps Submission objects to provide extra functionality"""

    _submission: Submission
    title: str
    subreddit: str
    url: str
    author: str
    nsfw: bool
    score: int
    # created_utc: ???
    urls: Set[str]
    response: httpx.Response
    can_unsave: bool

    def __init__(
        self, submission: Submission, client: httpx.AsyncClient, dry: bool = True
    ):
        self._submission = submission

        # relevant to user
        self.title = submission.title
        self.subreddit = str(submission.subreddit)
        self.url = submission.url
        self.author = str(submission.author)
        self.nsfw = submission.over_18
        self.score = submission.score
        self.created_utc = submission.created_utc
        self.urls = set()

        # relevant to parsing
        self.base_file_title = core.retitle(self._submission.title)
        self.response: httpx.Response = None

        # whether this post can be unsaved or not
        self.can_unsave = not dry

    async def find_urls(self, client: httpx.AsyncClient) -> None:
        self.urls = await parsers.find_urls(self.url, client)

    async def download_all(
        self,
        directory: str,
        client: httpx.AsyncClient,
        title: str = None,
        organize: bool = False,
    ) -> Dict[str, Optional[str]]:
        """
        Downloads all urls and bundles them with their results
        :param directory: directory in which to download each file
        :client: the httpx.AsyncClient to use for downloading
        :param title: title that the final file should have
        :param organize: whether or not to organize the download directory by subreddit
        :return: a dictionary where the keys are this submission's urls and the values are the
        filepaths to which those images were downloaded or None if the download failed
        """

        if not self.urls:
            return dict()
        if organize:
            directory = os.path.join(directory, self.subreddit)
        os.makedirs(directory, exist_ok=True)
        if not title:
            title = self.title
        urls_filepaths: Dict[str, Optional[str]] = dict()
        filename = title + core.get_extension(self.response)

        async def zip_result(url: str) -> Tuple[str, httpx.Response]:
            return (url, await client.get(url, timeout=10))

        urls_responses: List[Tuple[str, Optional[httpx.Response]]] = (
            await asyncio.gather(*(zip_result(url) for url in self.urls))
        )

        offset = 0
        for url, response in urls_responses:
            if response is None or response.status_code != 200:
                urls_filepaths[url] = None
                continue

            # Determine filename
            while filename in os.listdir(directory):
                offset += 1
                filename = f"{title} ({offset}){core.get_extension(self.response)}"

            destination = os.path.join(directory, filename)
            with open(destination, "wb") as image_file:
                image_file.write(response.content)
            urls_filepaths[url] = destination

        return urls_filepaths

    def log(self, file: str, exception: str = "") -> None:
        """
        Writes the given post's title and url to the specified file
        :param file: log file path
        """
        with open(file, "a", encoding="utf-8") as logfile:
            json.dump(
                {
                    "title": self._submission.title,
                    "id": self._submission.id,
                    "url": self._submission.url,
                    "recognized_urls": self.urls,
                    "exception": exception,
                },
                logfile,
            )

    def __str__(self) -> str:
        """
        Prints out information about the specified post
        :param index: the index number of the post
        :return: None
        """
        return f"{self.title} ({self.subreddit}) by {self.author} ({self.url})"
        # return self.format("%t\n   r/%s\n   %u\n   Saved %p / %f image(s) so far.")

    def summary_string(self) -> str:
        """Generates a string that summarizes this post"""
        return self.format("%t\n   r/%s\n   %u\n   Saved %p / %f image(s) so far.")

    def unsave(self, force=False) -> bool:
        """
        Unsaves this submission
        :param force: True to unsave this submission, even if can_unsave is False
        :return: True if the submission was unsaved, else False
        """
        if force or self.can_unsave:
            self._submission.unsave()
            return True
        return False

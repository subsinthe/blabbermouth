import random

import attr

from blabbermouth import thought
from blabbermouth.intelligence_core import IntelligenceCore
from blabbermouth.util.log import logged


@logged
@attr.s(slots=True)
class RedditChatter(IntelligenceCore):
    _reddit_browser = attr.ib()
    _top_post_comments = attr.ib()
    _subreddits_of_interest = attr.ib()
    _sort_types = attr.ib()

    async def conceive(self):
        subreddit = random.choice(self._subreddits_of_interest)
        sort_type = random.choice(self._sort_types)

        top_post = None
        async for post in self._reddit_browser.lookup_top_posts(
            subreddit, sort_type, limit=1
        ):
            top_post = post
            break
        else:
            self._log.warning("Top post was not found")
            return

        self._log.info("Top post of choice is {}".format(top_post))

        return thought.text(self._format_top_post_message(top_post))

    async def respond(self, *_):
        return None

    def _format_top_post_message(self, top_post):
        comment = random.choice(self._top_post_comments)
        return "{}\n{}".format(comment, top_post)

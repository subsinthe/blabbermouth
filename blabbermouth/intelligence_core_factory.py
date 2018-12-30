import datetime

from blabbermouth.aggregating_intelligence_core import (
    AggregatingIntelligenceCore,
)
from blabbermouth.markov_chain_intelligence_core import (
    MarkovChainIntelligenceCore,
)
from blabbermouth.reddit_browser import FeedSortType as RedditFeedSortType
from blabbermouth.reddit_browser import RedditBrowser
from blabbermouth.reddit_chatter import RedditChatter
from blabbermouth.speaking_intelligence_core import SpeakingIntelligenceCore
from blabbermouth.yandex_speech_client import Emotion as SpeechEmotion
from blabbermouth.yandex_speech_client import YandexSpeechClient


def build(
    chat_id,
    event_loop,
    knowledge_base,
    http_session,
    user_agent,
    markov_chain_worker,
    conf,
):
    markov_chain_core = MarkovChainIntelligenceCore.build(
        event_loop=event_loop,
        worker=markov_chain_worker,
        chat_id=chat_id,
        knowledge_base=knowledge_base,
        knowledge_lifespan=datetime.timedelta(
            minutes=conf["markov_chain_intelligence_core"][
                "knowledge_lifespan_minutes"
            ]
        ),
        make_sentence_attempts=conf["markov_chain_intelligence_core"][
            "make_sentence_attempts"
        ],
    )
    return AggregatingIntelligenceCore(
        cores=[
            markov_chain_core,
            SpeakingIntelligenceCore(
                text_core=markov_chain_core,
                speech_client=YandexSpeechClient(
                    http_session=http_session,
                    api_key=conf["yandex_dev_api_key"],
                    api_url=conf["yandex_speech_client"]["api_url"],
                ),
                voice=conf["speaking_intelligence_core"]["voice"],
                lang=conf["speaking_intelligence_core"]["lang"],
                audio_format=conf["speaking_intelligence_core"][
                    "audio_format"
                ],
                emotions=list(SpeechEmotion),
            ),
            RedditChatter(
                reddit_browser=RedditBrowser.build(
                    http_session=http_session,
                    reddit_url=conf["reddit_browser"]["reddit_url"],
                    user_agent=user_agent,
                ),
                top_post_comments=conf["reddit_chatter"]["top_post_comments"],
                subreddits_of_interest=conf["reddit_chatter"][
                    "subreddits_of_interest"
                ],
                sort_types=[
                    RedditFeedSortType.BEST,
                    RedditFeedSortType.HOT,
                    RedditFeedSortType.TOP,
                ],
            ),
        ]
    )

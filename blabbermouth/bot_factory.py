import datetime

import telepot
from telepot.aio.delegate import create_open, pave_event_space, per_chat_id

from blabbermouth import (
    chat_intelligence,
    chatter_handler,
    deaf_detector,
    learning_handler,
)
from blabbermouth.util import query_detector


def build(
    bot_token,
    bot_name,
    bot_accessor,
    event_loop,
    intelligence_registry,
    knowledge_base,
    telepot_http_timeout,
    conf,
):
    telepot.aio.DelegatorBot(
        bot_token,
        [
            _make_per_chat_handler(
                deaf_detector.DeafDetectorHandler,
                event_loop=event_loop,
                timeout=telepot_http_timeout,
            ),
            _make_per_chat_handler(
                chat_intelligence.ChatIntelligence,
                intelligence_registry=intelligence_registry,
                timeout=telepot_http_timeout,
            ),
            _make_per_chat_handler(
                learning_handler.LearningHandler,
                knowledge_base=knowledge_base,
                self_reference_detector=query_detector.self_reference_detector(
                    bot_name
                ),
                bot_name=bot_name,
                event_loop=event_loop,
                timeout=telepot_http_timeout,
            ),
            _make_per_chat_handler(
                chatter_handler.ChatterHandler,
                event_loop=event_loop,
                intelligence_registry=intelligence_registry,
                bot_accessor=bot_accessor,
                self_reference_detector=query_detector.self_reference_detector(
                    bot_name
                ),
                personal_query_detector=query_detector.personal_query_detector(
                    bot_name
                ),
                conceive_interval=datetime.timedelta(
                    hours=conf["chatter_handler"]["conceive_interval_hours"]
                ),
                callback_lifespan=datetime.timedelta(
                    days=conf["chatter_handler"]["callback_lifespan_days"]
                ),
                answer_placeholder=conf["chatter_handler"][
                    "answer_placeholder"
                ],
                timeout=telepot_http_timeout,
            ),
        ],
    )


def _make_per_chat_handler(handler, **kwargs):
    return pave_event_space()(per_chat_id(), create_open, handler, **kwargs)

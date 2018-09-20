import argparse
import asyncio
import concurrent.futures
import functools

import aiohttp
import attr
import telepot

from telepot.aio.loop import MessageLoop

import bot_factory
import chat_intelligence
import intelligence_core_factory
from mongo_knowledge_base import MongoKnowledgeBase
from util import config, log


@attr.s(slots=True)
class BotAccessor:
    _bot = attr.ib(default=None)

    def set(self, bot):
        self._bot = bot

    def __call__(self):
        assert self._bot is not None, "Bot has not been created yet"
        return self._bot


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", required=True)
    parser.add_argument("--yandex-dev-api-key", required=True)
    parser.add_argument("--dev", action="store_true")
    return parser.parse_args()


async def main(event_loop):
    args = parse_args()
    config_env_overrides = {
        "is_prod": not args.dev,
        "token": args.token,
        "yandex_dev_api_key": args.yandex_dev_api_key,
    }
    conf = config.load_config("config", "env.yaml", config_env_overrides)

    log.setup_logging(conf)

    telepot.aio.api.set_proxy(conf["core"]["proxy"])

    knowledge_base = MongoKnowledgeBase.build(
        host=conf["mongo_knowledge_base"]["db_host"],
        port=conf["mongo_knowledge_base"]["db_port"],
        db_name=conf["mongo_knowledge_base"]["db_name"],
        db_collection=conf["mongo_knowledge_base"]["db_collection"],
    )

    intelligence_registry = chat_intelligence.IntelligenceRegistry(
        core_constructor=functools.partial(
            intelligence_core_factory.build,
            event_loop=event_loop,
            knowledge_base=knowledge_base,
            http_session=aiohttp.ClientSession(),
            user_agent=conf["core"]["user_agent"],
            markov_chain_worker=concurrent.futures.ThreadPoolExecutor(max_workers=5),
            conf=conf,
        )
    )

    bot_accessor = BotAccessor()
    bot_accessor.set(
        bot_factory.build(
            bot_token=conf["token"],
            bot_name=conf["bot_name"],
            bot_accessor=bot_accessor,
            event_loop=event_loop,
            intelligence_registry=intelligence_registry,
            knowledge_base=knowledge_base,
            telepot_http_timeout=conf["telepot"]["http_timeout"],
            conf=conf,
        )
    )

    await MessageLoop(bot_accessor()).run_forever()


def run_main():
    event_loop = asyncio.get_event_loop()
    event_loop.create_task(main(event_loop))
    event_loop.run_forever()


if __name__ == "__main__":
    run_main()

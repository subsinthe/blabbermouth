import attr
import numpy
import telepot

from blabbermouth.util.chain import chained, not_none
from blabbermouth.util.log import logged


@logged
class IntentionalReplierHandler(telepot.aio.helper.ChatHandler):
    def __init__(
        self, *args, event_loop, intelligence_registry, reply_chance, **kwargs
    ):
        super(IntentionalReplierHandler, self).__init__(*args, **kwargs)

        self._event_loop = event_loop
        self._impl = Impl(
            intelligence_registry=intelligence_registry,
            reply_chance=reply_chance,
        )

        self._log.info("Created {}".format(id(self)))

    async def on_chat_message(self, message):
        self._event_loop.create_task(self._on_chat_message(message))

    @chained
    async def _on_chat_message(self, message):
        answer = not_none(self._impl.try_reply(message))
        await self.sender.sendMessage(
            answer, reply_to_message_id=message["message_id"]
        )

    def on__idle(self, _):
        self._log.debug("Ignoring on__idle")


@attr.s
class Impl:
    _intelligence_registry = attr.ib()
    _reply_chance = attr.ib()
    _random = attr.ib(factory=numpy.random.RandomState)

    async def try_reply(self):
        intelligence_core = self._intelligence_registry.get_core(self.chat_id)

        thought = await intelligence_core.conceive()
        if thought is None:
            self._log.info("No new thoughts from intellegence core")
            return

        return thought if _chance(self._random, self._reply_chance) else None


def _chance(random, probability=0.5):
    return random.choice([True, False], p=[probability, 1.0 - probability])

import attr
import telepot

from blabbermouth.util.log import logged


@attr.s(slots=True)
class IntelligenceRegistry:
    _core_constructor = attr.ib()
    _cores = attr.ib(factory=dict)

    def create_core(self, chat_id):
        self._cores[chat_id] = self._core_constructor(chat_id)

    def get_core(self, chat_id):
        return self._cores[chat_id]


@logged
class ChatIntelligence(telepot.aio.helper.ChatHandler):
    def __init__(self, *args, intelligence_registry, **kwargs):
        super(ChatIntelligence, self).__init__(*args, **kwargs)

        intelligence_registry.create_core(self.chat_id)

        self._log.info("Created {}".format(id(self)))

    async def on_chat_message(self, message):
        pass

    def on__idle(self, _):
        self._log.debug("Ignoring on__idle")

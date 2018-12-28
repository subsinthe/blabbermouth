import telepot
from blabbermouth.knowledge_base import KnowledgeBase
from blabbermouth.util.log import logged


@logged
class LearningHandler(telepot.aio.helper.ChatHandler):
    def __init__(self, *args, knowledge_base, self_reference_detector, bot_name, event_loop, **kwargs):
        if not isinstance(knowledge_base, KnowledgeBase):
            raise TypeError("knowledge_base must be KnowledgeBase")

        super(LearningHandler, self).__init__(*args, **kwargs)

        self._knowledge_base = knowledge_base
        self._self_reference_detector = self_reference_detector
        self._bot_name = bot_name
        self._event_loop = event_loop

        self._log.info("Created {}".format(id(self)))

    async def on_chat_message(self, message):
        self._event_loop.create_task(self._on_chat_message(message))

    async def _on_chat_message(self, message):
        text = message.get("text")
        if text is None:
            return
        if self._self_reference_detector(message):
            return

        user = message["from"]["username"]
        if user == self._bot_name:
            return

        chat_id = message["chat"]["id"]

        await self._knowledge_base.record(chat_id=chat_id, user=user, text=text)

    def on__idle(self, _):
        self._log.debug("Ignoring on__idle")

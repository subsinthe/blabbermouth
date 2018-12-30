import datetime
import functools
import random

import telepot

from blabbermouth.callback_query import CallbackQuery
from blabbermouth.markup import InlineButton
from blabbermouth.thought import Type as ThoughtType
from blabbermouth.thought import text as thought_text
from blabbermouth.util.chain import chained, check, not_none
from blabbermouth.util.log import logged
from blabbermouth.util.timer import Timer


@logged
class ChatterHandler(telepot.aio.helper.ChatHandler):
    def __init__(
        self,
        *args,
        event_loop,
        intelligence_registry,
        bot_accessor,
        self_reference_detector,
        personal_query_detector,
        conceive_interval,
        callback_lifespan,
        answer_placeholder,
        **kwargs
    ):
        super(ChatterHandler, self).__init__(
            *args, include_callback_query=True, **kwargs
        )

        self._event_loop = event_loop
        self._intelligence_registry = intelligence_registry
        self._bot_accessor = bot_accessor
        self._self_reference_detector = self_reference_detector
        self._personal_quary_detector = personal_query_detector
        self._conceive_interval = conceive_interval
        self._conceive_timer = Timer(
            callback=self._conceive,
            interval=self._randomize_conceive_interval(),
        )
        self._answer_placeholder = thought_text(answer_placeholder)

        self._callback_query = CallbackQuery(
            callback_lifespan=callback_lifespan
        )
        self.on_callback_query = self._callback_query.on_callback_query

        self._log.info("Created {}".format(id(self)))

    async def on_chat_message(self, message):
        self._event_loop.create_task(self._on_chat_message(message))

    @chained
    async def _on_chat_message(self, message):
        check(self._self_reference_detector(message))
        source = not_none(message.get("from"))
        user = not_none(source.get("username"))

        self._log.info(
            "User {} in chat {} is talking to me".format(user, self.chat_id)
        )

        intelligence_core = self._intelligence_registry.get_core(self.chat_id)

        answer = await intelligence_core.respond(
            user=user, message=message.get("text", "")
        )
        if answer is None:
            self._log.info('Got "None" answer from intelligence core')
            answer = self._answer_placeholder

        await self._send_thought(answer)

    def on__idle(self, _):
        self._log.debug("Ignoring on__idle")

    async def _conceive(self):
        intelligence_core = self._intelligence_registry.get_core(self.chat_id)

        thought = await intelligence_core.conceive()
        if thought is None:
            self._log.info("No new thoughts from intellegence core")
            return

        await self._send_thought(thought)

        self._conceive_timer.interval = self._randomize_conceive_interval()

    def _randomize_conceive_interval(self):
        return datetime.timedelta(
            seconds=random.uniform(0, self._conceive_interval.total_seconds())
        )

    async def _send_thought(self, thought):
        if thought.thought_type == ThoughtType.TEXT:
            await self.sender.sendMessage(thought.payload)
        elif thought.thought_type == ThoughtType.SPEECH:
            await self.sender.sendVoice(
                thought.payload["speech_data"],
                reply_markup=InlineButton(
                    text="Read",
                    callback_data=self._callback_query.register_handler(
                        functools.partial(
                            self._read_voice_message_handler,
                            voice_text=thought.payload["text"],
                        )
                    ),
                ),
            )
        else:
            raise ValueError(
                "Unexpected thought type: {}".format(thought.thought_type)
            )

    async def _read_voice_message_handler(self, query_id, voice_text):
        await self._bot_accessor().answerCallbackQuery(
            query_id, text=voice_text, show_alert=True
        )

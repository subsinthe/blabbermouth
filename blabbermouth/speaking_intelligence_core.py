import io
import random

import attr

from blabbermouth import thought
from blabbermouth.intelligence_core import IntelligenceCore
from blabbermouth.util.chain import chained, not_none
from blabbermouth.util.log import logged


@logged
@attr.s(slots=True)
class SpeakingIntelligenceCore(IntelligenceCore):
    _text_core = attr.ib(validator=attr.validators.instance_of(IntelligenceCore))
    _speech_client = attr.ib()
    _voice = attr.ib()
    _lang = attr.ib()
    _audio_format = attr.ib()
    _emotions = attr.ib()

    @chained
    async def conceive(self):
        return await self._make_voice(self._extract_text(not_none(await self._text_core.conceive())))

    @chained
    async def respond(self, user, message):
        return await self._make_voice(
            self._extract_text(not_none(await self._text_core.respond(user, message)))
        )

    async def _make_voice(self, text):
        emotion = random.choice(self._emotions)

        self._log.info("Using {} emotion".format(emotion))

        response = await self._speech_client.vocalize(
            text=text, voice=self._voice, lang=self._lang, audio_format=self._audio_format, emotion=emotion
        )
        return thought.speech(text_data=text, speech_data=io.BytesIO(response))

    @staticmethod
    def _extract_text(core_response):
        if core_response.thought_type is not thought.Type.TEXT:
            raise ValueError(
                "Wrapped core generated unexpected thought type: {}".format(core_response.thought_type)
            )
        return core_response.payload

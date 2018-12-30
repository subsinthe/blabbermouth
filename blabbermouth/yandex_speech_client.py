import enum

import attr


class Emotion(enum.Enum):
    NEUTRAL = "neutral"
    GOOD = "good"
    EVIL = "evil"


@attr.s(slots=True)
class YandexSpeechClient:
    _http_session = attr.ib()
    _api_url = attr.ib()
    _api_key = attr.ib()

    async def vocalize(self, text, voice, lang, audio_format, emotion):
        params = {
            "key": self._api_key,
            "text": text,
            "speaker": voice,
            "lang": lang,
            "format": audio_format,
            "emotion": emotion.value,
        }
        async with self._http_session.get(
            self._api_url, params=params
        ) as response:
            if response.status != 200:
                raise Exception(
                    "Got unwanted response {}: {}".format(
                        response.status, await response.text()
                    )
                )
            return await response.read()

import enum

import attr


class Type(enum.Enum):
    TEXT = enum.auto()
    SPEECH = enum.auto()


@attr.s(slots=True, frozen=True)
class _Thought:
    thought_type = attr.ib()
    payload = attr.ib()


def text(text_data):
    return _Thought(thought_type=Type.TEXT, payload=text_data)


def speech(text_data, speech_data):
    return _Thought(
        thought_type=Type.SPEECH,
        payload={"text": text_data, "speech_data": speech_data},
    )

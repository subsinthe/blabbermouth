import contextlib
import enum
import functools
import random

import attr
import markovify

from blabbermouth import thought
from blabbermouth.intelligence_core import IntelligenceCore
from blabbermouth.knowledge_base import KnowledgeBase
from blabbermouth.util.lifespan import Lifespan
from blabbermouth.util.log import logged


async def _strip_dots(iterable):
    async for entry in iterable:
        if entry.endswith("."):
            yield entry[:-1]
        yield entry


async def _async_join(iterable, sep):
    sep = sep.encode("utf-8")
    b = bytearray()
    try:
        b += (await iterable.__anext__()).encode("utf-8")
    except StopAsyncIteration:
        return ""
    async for s in iterable:
        b += sep
        b += s.encode("utf-8")
    return b.decode("utf-8")


@logged
@attr.s(slots=True)
class CachedMarkovText:
    _event_loop = attr.ib()
    _worker = attr.ib()
    _knowledge_source = attr.ib()
    _make_sentence_attempts = attr.ib()
    _text_lifespan = attr.ib(converter=Lifespan)
    _text = attr.ib(factory=lambda: markovify.Text("."))
    _sentence_is_building = attr.ib(default=False)

    def __attrs_post_init__(self):
        self._schedule_new_text()

    async def make_sentence(self):
        if not self._text_lifespan:
            self._schedule_new_text()

        if self._sentence_is_building:
            self._log.info("Sentence is building")
            return None

        sentence = None
        with self._sentence_building_session():
            sentence = await self._build_sentence()
            if sentence is None:
                self._log.error("Failed to produce sentence")

        return sentence

    def _schedule_new_text(self):
        self._event_loop.create_task(self._build_text())
        self._text_lifespan.reset()

    async def _build_text(self):
        knowledge = await _async_join(
            _strip_dots(self._knowledge_source()), sep=". "
        )
        self._text = await self._event_loop.run_in_executor(
            self._worker, lambda: markovify.Text(knowledge)
        )
        self._log.info("Successfully built new text")

    @contextlib.contextmanager
    def _sentence_building_session(self):
        self._sentence_is_building = True
        try:
            yield
        except Exception as ex:
            self._log.error(
                "[CachedMarkovText] Failed to build sentence: {}".format(ex)
            )
        finally:
            self._sentence_is_building = False

    async def _build_sentence(self):
        text = self._text
        make_sentence_attempts = self._make_sentence_attempts
        return await self._event_loop.run_in_executor(
            self._worker,
            lambda: text.make_sentence(tries=make_sentence_attempts),
        )


@logged
@attr.s(slots=True)
class MarkovChainIntelligenceCore(IntelligenceCore):
    class Strategy(enum.Enum):
        BY_CURRENT_CHAT = enum.auto()
        BY_CURRENT_USER = enum.auto()
        BY_FULL_KNOWLEDGE = enum.auto()

    _knowledge_base = attr.ib(
        validator=attr.validators.instance_of(KnowledgeBase)
    )
    _text_constructor = attr.ib()
    _markov_texts = attr.ib()

    @classmethod
    def build(
        cls,
        event_loop,
        worker,
        chat_id,
        knowledge_base,
        knowledge_lifespan,
        make_sentence_attempts,
    ):
        text_constructor = functools.partial(
            CachedMarkovText,
            event_loop=event_loop,
            worker=worker,
            make_sentence_attempts=make_sentence_attempts,
            text_lifespan=knowledge_lifespan,
        )
        return cls(
            knowledge_base=knowledge_base,
            text_constructor=text_constructor,
            markov_texts={
                cls.Strategy.BY_CURRENT_CHAT: text_constructor(
                    knowledge_source=functools.partial(
                        knowledge_base.select_by_chat, chat_id
                    )
                ),
                cls.Strategy.BY_FULL_KNOWLEDGE: text_constructor(
                    knowledge_source=knowledge_base.select_by_full_knowledge
                ),
            },
        )

    async def conceive(self):
        response = await self._form_message(
            strategies=[
                self.Strategy.BY_CURRENT_CHAT,
                self.Strategy.BY_FULL_KNOWLEDGE,
            ]
        )
        return thought.text(response) if response is not None else None

    async def respond(self, user, message):
        response = await self._form_message(
            strategies=[
                self.Strategy.BY_CURRENT_CHAT,
                self.Strategy.BY_CURRENT_USER,
                self.Strategy.BY_FULL_KNOWLEDGE,
            ],
            user=user,
        )
        return thought.text(response) if response is not None else None

    async def _form_message(self, strategies, user=None):
        strategy = random.choice(strategies)
        if strategy == self.Strategy.BY_CURRENT_USER:
            text_key = (strategy, user)
            if text_key not in self._markov_texts:
                self._markov_texts[text_key] = self._text_constructor(
                    knowledge_source=functools.partial(
                        self._knowledge_base.select_by_user, user
                    )
                )
        else:
            text_key = strategy

        self._log.info("Using text for {}".format(text_key))

        return await self._markov_texts[text_key].make_sentence()

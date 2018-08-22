import contextlib
import enum
import random

import attr
import markovify

from blabbermouth.intelligence_core import IntelligenceCore
from blabbermouth.knowledge_base import KnowledgeBase
from blabbermouth.util.lifespan import Lifespan


@attr.s(slots=True)
class CachedMarkovText:
    knowledge_source = attr.ib()
    make_sentence_attempts = attr.ib(default=10)
    text_lifespan = attr.ib(converter=Lifespan)
    text = attr.ib(default=None)
    text_is_building = attr.ib(default=False)

    async def make_sentence(self, knowledge_dependency):
        if self.text is None and self.text_is_building:
            print("[CachedMarkovText] First text is currently building")
            return None

        if self.text is None or not self.text_lifespan:
            with self._text_building_session():
                self.text = await self._build_text(knowledge_dependency)
                self.text_lifespan.reset()

        sentence = self.text.make_sentence(tries=self.make_sentence_attempts)
        if sentence is None:
            print("[CachedMarkovText]: Failed to make sentence")
        return sentence

    @contextlib.contextmanager
    def _text_building_session(self):
        self.text_is_building = True
        try:
            yield
        except Exception as ex:
            print("[CachedMarkovText] Failed to build markov text: {}".format(ex))
        finally:
            self.text_is_building = False

    async def _build_text(self, knowledge_dependency):
        print("[CachedMarkovText] Building new text")

        knowledge = ". ".join(sentence async for sentence in self.knowledge_source(knowledge_dependency))
        return markovify.Text(knowledge)


@attr.s(slots=True)
class MarkovChainIntelligenceCore(IntelligenceCore):
    class Strategy(enum.Enum):
        BY_CURRENT_CHAT = enum.auto()
        BY_CURRENT_USER = enum.auto()
        BY_FULL_KNOWLEDGE = enum.auto()

    chat_id = attr.ib()
    knowledge_base = attr.ib(validator=attr.validators.instance_of(KnowledgeBase))
    knowledge_lifespan = attr.ib()
    make_sentence_attempts = attr.ib()
    answer_placeholder = attr.ib()
    markov_texts_by_strategy = attr.ib(dict)

    def __attrs_post_init__(self):
        chat_id = self.chat_id

        self.markov_texts_by_strategy = {
            p[0]: CachedMarkovText(
                knowledge_source=p[1],
                knowledge_lifespan=self.knowledge_lifespan,
                make_sentence_attempts=self.make_sentence_attempts,
            )
            for p in [
                (self.Strategy.BY_CURRENT_CHAT, lambda _: self.knowledge_base.select_by_chat(chat_id)),
                (
                    self.Strategy.BY_CURRENT_USER,
                    lambda dependency: self.knowledge_base.select_by_user(dependency["user"]),
                ),
                (self.Strategy.BY_FULL_KNOWLEDGE, lambda _: self.knowledge_base.select_by_full_knowledge()),
            ]
        }

    async def conceive(self):
        return await self._form_message(
            strategies=[self.Strategy.BY_CURRENT_CHAT, self.Strategy.BY_FULL_KNOWLEDGE], dependency={}
        )

    async def respond(self, user, message):
        return await self._form_message(
            strategies=[
                self.Strategy.BY_CURRENT_CHAT,
                self.Strategy.BY_CURRENT_USER,
                self.Strategy.BY_FULL_KNOWLEDGE,
            ],
            dependency={"user": user},
        )

    async def _form_message(self, strategies, dependency):
        strategy = random.choice(strategies)

        print("[MarkovChainIntelligenceCore] Using {} strategy".format(strategy))

        sentence = await self.markov_texts_by_strategy[strategy].make_sentence(dependency)
        return sentence if sentence is not None else self.answer_placeholder

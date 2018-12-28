import attr

import motor.motor_asyncio
from blabbermouth.knowledge_base import KnowledgeBase


@attr.s(slots=True)
class MongoKnowledgeBase(KnowledgeBase):
    _client = attr.ib()
    _collection = attr.ib()

    @classmethod
    def build(cls, host, port, db_name, db_collection):
        client = motor.motor_asyncio.AsyncIOMotorClient(host, port)
        return cls(client=client, collection=client[db_name][db_collection])

    async def record(self, chat_id, user, text):
        doc = {"chat_id": chat_id, "user": user, "text": text}
        await self._collection.insert_one(doc)

    async def select_by_chat(self, chat_id):
        async for doc in self._collection.find({"chat_id": chat_id}):
            yield doc["text"]

    async def select_by_user(self, user):
        async for doc in self._collection.find({"user": user}):
            yield doc["text"]

    async def select_by_full_knowledge(self):
        async for doc in self._collection.find({}):
            yield doc["text"]

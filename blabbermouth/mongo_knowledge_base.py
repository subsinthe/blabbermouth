import motor.motor_asyncio

from knowledge_base import KnowledgeBase


class MongoKnowledgeBase(KnowledgeBase):
    def __init__(self, host, port, db_name, db_collection):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(host, port)
        self._collection = self._client[db_name][db_collection]

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

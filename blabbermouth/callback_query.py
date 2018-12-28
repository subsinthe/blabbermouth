import attr

import telepot
from blabbermouth.util.chain import chained, not_none
from blabbermouth.util.lifespan import Lifespan


@attr.s(slots=True)
class CallbackQuery:
    @attr.s(slots=True, frozen=True)
    class CallbackData:
        handler = attr.ib()
        lifespan = attr.ib(converter=Lifespan)

    _callback_lifespan = attr.ib()
    _callback_data_storage = attr.ib(factory=dict)

    def register_handler(self, handler):
        callback_data = self.CallbackData(handler=handler, lifespan=self._callback_lifespan)
        data_id = id(callback_data)

        self._callback_data_storage[data_id] = callback_data

        return str(data_id)

    @chained
    async def on_callback_query(self, message):
        query_id, _, lowlevel_user_data = telepot.glance(message, flavor="callback_query")
        callback_data_key = int(lowlevel_user_data)
        data = not_none(self._callback_data_storage.get(callback_data_key))
        if not data.lifespan:
            self._callback_data_storage.pop(callback_data_key)

        await data.handler(query_id)

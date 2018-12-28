import random

import attr

from blabbermouth.intelligence_core import IntelligenceCore
from blabbermouth.util.log import logged


@logged
@attr.s(slots=True)
class AggregatingIntelligenceCore(IntelligenceCore):
    _cores = attr.ib()

    async def conceive(self):
        return await self._try_cores(lambda core: core.conceive())

    async def respond(self, user, message):
        return await self._try_cores(lambda core: core.respond(user, message))

    async def _try_cores(self, coro):
        cores = self._cores.copy()
        random.shuffle(cores)
        for core in cores:
            try:
                result = await coro(core)
            except Exception as ex:
                self._log.exception(ex)
            else:
                if result is not None:
                    return result
        return None

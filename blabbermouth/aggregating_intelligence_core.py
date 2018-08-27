import random

import attr

from intelligence_core import IntelligenceCore


@attr.s
class AggregatingIntelligenceCore(IntelligenceCore):
    cores = attr.ib()

    async def conceive(self):
        return await self._try_cores(lambda core: core.conceive())

    async def respond(self, user, message):
        return await self._try_cores(lambda core: core.respond(user, message))

    async def _try_cores(self, coro):
        cores = self.cores.copy()
        random.shuffle(cores)
        for core in cores:
            result = await coro(core)
            if result is not None:
                return result
        return None

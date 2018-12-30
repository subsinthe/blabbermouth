import datetime
import time

import attr


@attr.s(slots=True)
class Lifespan:
    _timeout = attr.ib(
        validator=attr.validators.instance_of(datetime.timedelta)
    )
    _stamp = attr.ib(factory=time.time)

    def __bool__(self):
        return (
            datetime.timedelta(seconds=(time.time() - self._stamp))
            < self._timeout
        )

    def reset(self):
        self._stamp = time.time()

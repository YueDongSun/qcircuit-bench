"""Task id rules.

See ``docs/adr/0002-task-format.md``. The family may contain underscores
(``cf_t2_001_laf3_er_levels``). The number is the three-digit token before the
slug.
"""

import re

TASK_ID_RE = re.compile(
    r"^(?P<family>[a-z][a-z0-9]*(?:_[a-z][a-z0-9]*)*)"
    r"_(?P<number>\d{3})_(?P<slug>[a-z][a-z0-9_]*)$"
)

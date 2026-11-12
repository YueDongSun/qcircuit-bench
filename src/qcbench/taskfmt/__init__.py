"""Task-format validator and scaffolder.

See ``docs/adr/0002-task-format.md`` and ``spec/TASKS.md``.
"""

from qcbench.taskfmt.scaffold import scaffold_task
from qcbench.taskfmt.validate import (
    TaskFormatError,
    TaskMeta,
    heading_slug,
    validate_task,
    validate_tasks,
)

__all__ = [
    "TaskFormatError",
    "TaskMeta",
    "heading_slug",
    "scaffold_task",
    "validate_task",
    "validate_tasks",
]

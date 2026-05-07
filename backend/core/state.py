from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class AgentState:

    task: str

    current_step: int = 0

    completed: bool = False

    memory: List[Dict[str, Any]] = field(
        default_factory=list
    )

    actions: List[Dict[str, Any]] = field(
        default_factory=list
    )

    outputs: List[Dict[str, Any]] = field(
        default_factory=list
    )

    workspace: str = ""

    errors: List[str] = field(
        default_factory=list
    )

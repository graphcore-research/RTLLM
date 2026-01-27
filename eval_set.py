from pathlib import Path
from typing import Iterable

from ..eval_set import Problem


class RTLLMV2EvalSet:
    def __init__(self):
        self._base_dir = Path(__file__).parent

    def get_problems(self) -> Iterable[Problem]:
        for desc_file in sorted(self._base_dir.glob("**/design_description.txt")):
            yield Problem(
                eval_set="rtllm_v2",
                name=desc_file.parent.name,
                system_prompt="Please act as a professional verilog designer.",
                user_prompt=desc_file.read_text(),
            )

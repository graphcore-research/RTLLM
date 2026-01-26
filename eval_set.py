from pathlib import Path
from typing import Iterable, Tuple


class RTLLMV1_1EvalSet:
    def __init__(self):
        self._base_dir = Path(__file__).parent

    def get_prompts(self) -> Iterable[Tuple[str, str]]:
        for desc_file in sorted(self._base_dir.glob("*/design_description.txt")):
            problem_name = desc_file.parent.name
            yield (problem_name, desc_file.read_text())

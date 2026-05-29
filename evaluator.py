import shutil
import tempfile
from pathlib import Path

from post_training_torchtitan.app.grading import FormatReward, FormatRewardResult

from ..async_util import run_with_timeout
from ..evaluator import EvalResult, Sample

_THIS_DIR = Path(__file__).parent

_FORMAT_REWARD = FormatReward()


def _score_format(completion: str) -> FormatRewardResult:
    return _FORMAT_REWARD.score(completion)


def _format_details(format_result: FormatRewardResult) -> dict[str, object]:
    return {
        "format_passed": format_result.passed,
        "format_reward": format_result.reward,
        "format_failure_reason": format_result.failure_reason,
        "extracted_code": format_result.code,
    }


async def evaluate(sample: Sample) -> EvalResult:
    design_dir = _THIS_DIR / sample.problem
    log_parts = []

    format_result = _score_format(sample.code)
    code = format_result.code
    format_details = _format_details(format_result)
    if not format_result.passed:
        reason = "format error"
        log = f"=== format ===\n{format_result.failure_reason}"
        return EvalResult(
            passed=False,
            details={
                **format_details,
                "syntax_passed": False,
                "func_passed": False,
                "reason": reason,
                "log": log,
            },
        )

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        work_dir = tmp_dir / sample.problem
        shutil.copytree(design_dir, work_dir)
        shutil.copy(_THIS_DIR / "common.mk", tmp_dir / "common.mk")

        # Write the code to be tested
        (work_dir / f"{sample.problem}.v").write_text(code)

        # Compile
        completed, compile_output = await run_with_timeout("make vcs", cwd=work_dir)
        log_parts.append(f"=== make vcs ===\n{compile_output}")
        syntax_passed = (work_dir / "simv").exists()

        func_passed = False
        if syntax_passed:
            completed, sim_output = await run_with_timeout("make sim", cwd=work_dir)
            log_parts.append(f"=== make sim ===\n{sim_output}")
            if completed:
                func_passed = "Pass" in sim_output or "pass" in sim_output

        return EvalResult(
            passed=syntax_passed and func_passed,
            details={
                **format_details,
                "syntax_passed": syntax_passed,
                "func_passed": func_passed,
                "log": "\n\n".join(log_parts),
            },
        )

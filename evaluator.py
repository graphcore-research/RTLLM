import shutil
import tempfile
from pathlib import Path

from ..async_util import run_with_timeout
from ..evaluator import EvalResult, Sample

_THIS_DIR = Path(__file__).parent

# Build lookup table: design name -> relative path from _THIS_DIR
_DESIGN_PATHS: dict[str, Path] = {}
for makefile in _THIS_DIR.glob("**/makefile"):
    design_dir = makefile.parent
    design_name = design_dir.name
    _DESIGN_PATHS[design_name] = design_dir


async def evaluate(sample: Sample) -> EvalResult:
    design_dir = _DESIGN_PATHS.get(sample.problem)
    if design_dir is None:
        raise ValueError(f"Unknown design: {sample.problem}")

    log_parts = []

    # Extract code from markdown code fences if present
    code = sample.code
    if '```verilog' in code or '```systemverilog' in code or '```' in code:
        # Find the first verilog code block
        for fence in ['```verilog', '```systemverilog', '```']:
            if fence in code:
                # Split at the opening fence
                parts = code.split(fence, 1)
                if len(parts) >= 2:
                    # Everything after the opening fence
                    after_fence = parts[1]
                    # Find the closing fence
                    if '```' in after_fence:
                        code = after_fence.split('```', 1)[0].strip()
                        break

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        work_dir = tmp_dir / sample.problem
        shutil.copytree(design_dir, work_dir)
        shutil.copy(_THIS_DIR / "common.mk", work_dir / "common.mk")

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
                "syntax_passed": syntax_passed,
                "func_passed": func_passed,
                "log": "\n\n".join(log_parts),
            },
        )

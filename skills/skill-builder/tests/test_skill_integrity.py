"""Guard against known broken shell patterns in SKILL.md files."""

from pathlib import Path
import pytest

_SKILLS_ROOT = Path(__file__).parent.parent.parent  # agent-dev/skills/

_SKILL_MDS = sorted(_SKILLS_ROOT.glob("*/SKILL.md"))


@pytest.mark.parametrize("skill_md", _SKILL_MDS, ids=lambda p: p.parent.name)
def test_no_claude_skill_dir_shell_var(skill_md: Path) -> None:
    """`${CLAUDE_SKILL_DIR}` is unset in bash and expands to empty string.

    Commands that embed it silently resolve to wrong paths (e.g. /eval-viewer/…),
    causing the server to never start and the viewer to show empty content.
    Use the '<skill-builder-dir>' placeholder instead and instruct the LLM to
    substitute the actual base directory shown at the top of its skill context.
    """
    content = skill_md.read_text(encoding="utf-8")
    assert "${CLAUDE_SKILL_DIR}" not in content, (
        f"{skill_md.relative_to(_SKILLS_ROOT)}: contains ${{CLAUDE_SKILL_DIR}} "
        "which expands to empty string in bash. "
        "Replace with '<skill-builder-dir>' placeholder."
    )

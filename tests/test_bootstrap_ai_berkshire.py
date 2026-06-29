from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


REPO_ROOT = Path("/Users/hyungjooyi/ai-berkshire")
SCRIPT_PATH = REPO_ROOT / "scripts" / "bootstrap_ai_berkshire.py"


def load_module():
    spec = importlib.util.spec_from_file_location("bootstrap_ai_berkshire", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class Recorder:
    def __init__(self):
        self.calls = []

    def __call__(self, command, check=False, cwd=None):
        self.calls.append((tuple(command), check, cwd))
        return None


def test_bootstrap_check_mode_runs_validation_commands_only(tmp_path):
    mod = load_module()
    recorder = Recorder()
    config = mod.BootstrapConfig(
        repo_root=REPO_ROOT,
        codex_home=tmp_path / ".codex",
        claude_commands_dir=tmp_path / ".claude" / "commands",
        command_runner=recorder,
        check=True,
    )

    result = mod.bootstrap(config)

    assert result["mode"] == "check"
    assert recorder.calls == [
        (("python3", "scripts/sync-codex-skills.py", "--check"), True, str(REPO_ROOT)),
        (("python3", "scripts/sync-codex-prompts.py", "--check"), True, str(REPO_ROOT)),
    ]
    assert not (tmp_path / ".codex").exists()
    assert not (tmp_path / ".claude").exists()


def test_bootstrap_installs_codex_and_claude_surfaces(tmp_path):
    mod = load_module()
    recorder = Recorder()
    codex_home = tmp_path / ".codex"
    claude_dir = tmp_path / ".claude" / "commands"
    config = mod.BootstrapConfig(
        repo_root=REPO_ROOT,
        codex_home=codex_home,
        claude_commands_dir=claude_dir,
        command_runner=recorder,
    )

    result = mod.bootstrap(config)

    assert result["mode"] == "install"
    assert (codex_home / "skills" / "investment-research" / "SKILL.md").exists()
    assert (codex_home / "prompts" / "investment-research.md").exists()
    assert (claude_dir / "investment-research.md").exists()
    assert recorder.calls[0][0] == ("python3", "scripts/sync-codex-skills.py")
    assert recorder.calls[1][0] == ("python3", "scripts/sync-codex-prompts.py")

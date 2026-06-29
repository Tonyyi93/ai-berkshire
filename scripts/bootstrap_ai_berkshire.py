#!/usr/bin/env python3
"""Bootstrap the AI Berkshire workspace for Claude Code and Codex.

This is the single entrypoint for "make AI Berkshire runnable":
- validate or regenerate Codex skill/prompt artifacts from `skills/`
- install Claude commands
- install Codex skills and slash prompts
- keep local tool scripts executable
"""

from __future__ import annotations

from dataclasses import dataclass
import argparse
from pathlib import Path
from shutil import copy2, copytree, rmtree
from subprocess import run
from typing import Callable


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class BootstrapConfig:
    repo_root: Path = ROOT
    codex_home: Path = Path.home() / ".codex"
    claude_commands_dir: Path = Path.home() / ".claude" / "commands"
    command_runner: Callable[..., object] = run
    check: bool = False
    dry_run: bool = False
    install_claude: bool = True
    install_codex: bool = True
    install_prompts: bool = True


def _sync_commands(check: bool, repo_root: Path) -> list[list[str]]:
    suffix = ["--check"] if check else []
    return [
        ["python3", "scripts/sync-codex-skills.py", *suffix],
        ["python3", "scripts/sync-codex-prompts.py", *suffix],
    ]


def _copy_skill_dirs(repo_root: Path, codex_home: Path) -> list[Path]:
    copied: list[Path] = []
    source_root = repo_root / "codex-skills"
    dest_root = codex_home / "skills"
    dest_root.mkdir(parents=True, exist_ok=True)

    for source in sorted(source_root.iterdir()):
        if not source.is_dir():
            continue
        target = dest_root / source.name
        if target.exists():
            rmtree(target)
        copytree(source, target)
        copied.append(target)
    return copied


def _copy_prompts(repo_root: Path, codex_home: Path) -> list[Path]:
    copied: list[Path] = []
    source_root = repo_root / "codex-prompts"
    dest_root = codex_home / "prompts"
    dest_root.mkdir(parents=True, exist_ok=True)

    for source in sorted(source_root.glob("*.md")):
        target = dest_root / source.name
        copy2(source, target)
        copied.append(target)
    return copied


def _install_claude(repo_root: Path, commands_dir: Path) -> list[Path]:
    commands_dir.mkdir(parents=True, exist_ok=True)
    copied: list[Path] = []
    for source in sorted((repo_root / "skills").glob("*.md")):
        target = commands_dir / source.name
        copy2(source, target)
        copied.append(target)
    return copied


def bootstrap(config: BootstrapConfig) -> dict[str, object]:
    commands = _sync_commands(config.check, config.repo_root)
    for command in commands:
        config.command_runner(command, check=True, cwd=str(config.repo_root))

    if config.check or config.dry_run:
        return {"mode": "check" if config.check else "dry-run", "commands": commands}

    copied: list[Path] = []
    if config.install_codex:
        copied.extend(_copy_skill_dirs(config.repo_root, config.codex_home))
    if config.install_prompts:
        copied.extend(_copy_prompts(config.repo_root, config.codex_home))
    if config.install_claude:
        copied.extend(_install_claude(config.repo_root, config.claude_commands_dir))

    for tool in sorted((config.repo_root / "tools").glob("*")):
        if tool.suffix in {".py", ".sh"} and tool.exists():
            tool.chmod(tool.stat().st_mode | 0o111)

    return {
        "mode": "install",
        "commands": commands,
        "copied": [str(path) for path in copied],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bootstrap_ai_berkshire")
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--codex-home", type=Path, default=Path.home() / ".codex")
    parser.add_argument("--claude-commands-dir", type=Path, default=Path.home() / ".claude" / "commands")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-claude", action="store_true", help="Skip installing Claude commands")
    parser.add_argument("--no-codex", action="store_true", help="Skip installing Codex skills")
    parser.add_argument("--no-prompts", action="store_true", help="Skip installing Codex prompts")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = bootstrap(
        BootstrapConfig(
            repo_root=args.repo_root,
            codex_home=args.codex_home,
            claude_commands_dir=args.claude_commands_dir,
            check=args.check,
            dry_run=args.dry_run,
            install_claude=not args.no_claude,
            install_codex=not args.no_codex,
            install_prompts=not args.no_prompts,
        )
    )
    print(result["mode"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""open terminal"""

import os
import platform
import shlex
import subprocess
from pathlib import Path
from typing import Optional, List

import sublime
import sublime_plugin

TERMINAL_EMULATORS = {
    "Windows": "cmd",
    "Darwin": "zsh",
    "Linux": "xterm",
}

DEFAULT_TERMINAL = TERMINAL_EMULATORS[platform.system()]


def get_workspace_folder(view: sublime.View) -> Optional[Path]:
    file_name = view.file_name()
    if not file_name:
        return None

    folders = view.window().folders()
    candidates = [f for f in folders if file_name.startswith(f)]
    if candidates:
        return Path(max(candidates))

    return Path(file_name).parent


EnvironmentType = dict


def environ_update(old: EnvironmentType, new: EnvironmentType) -> EnvironmentType:
    """"""
    if not new:
        return old

    # Keep old data unchanged
    temp = dict(old)

    # PATH lookup start from begin to end
    paths = new["PATH"].split(os.pathsep) + old["PATH"].split(os.pathsep)

    temp_paths = []
    for path in paths:
        if path in temp_paths:
            # remove PATH redefinition
            continue

        temp_paths.append(path)

    temp.update(new)
    temp["PATH"] = os.pathsep.join(temp_paths)
    return temp


def fallback_path(path: Path) -> Path:
    if path.is_dir():
        return path
    return Path().home()


SETTINGS_BASENAME = "Terminal.sublime-settings"


class OpenTerminalCommand(sublime_plugin.WindowCommand):
    def run(
        self,
        path: str = "",
        # passed from 'Side Bar.sublime-menu'
        dirs: List[str] = None,
    ):
        entry_path = ""
        if path:
            entry_path = path
        elif dirs:
            # from 'Side Bar.sublime-menu'
            entry_path = dirs[0]
        else:
            # from active view
            entry_path = get_workspace_folder(self.window.active_view())

        envs = self.get_envs(dirs)
        emulator = self.get_emulator()
        self.open_terminal(emulator, envs, entry_path)

    def open_terminal(
        self,
        command: List[str],
        env: Optional[dict] = None,
        entry_path: Optional[str] = "",
    ):
        env = environ_update(os.environ, env)
        entry_path = fallback_path(Path(entry_path))
        try:
            subprocess.Popen(command, cwd=entry_path, env=env)
        except Exception as err:
            message = f"Error open terminal.\n   {shlex.join(command)}\n\n\nError: {err}"
            sublime.error_message(message)

    def get_emulator(self) -> List[str]:
        settings = sublime.load_settings(SETTINGS_BASENAME)
        emulator = settings.get("emulator") or DEFAULT_TERMINAL
        args = settings.get("arguments", "")
        return [emulator] + shlex.split(args)

    def get_envs(self, selected_dirs: List[str] = None):
        def get_envs(basename: str) -> Optional[dict]:
            settings = sublime.load_settings(basename)
            return settings.get("envs", None)

        if envs := get_envs(SETTINGS_BASENAME):
            return envs

        view = self.window.active_view()
        if selected_dirs:
            # ensure selected dirs is parent of active view path
            file_name = view.file_name()
            if not any((d for d in selected_dirs if file_name.startswith(d))):
                return None

        # get environemnt from active view syntax settings
        syntax = view.settings().get("syntax")
        settings_name = f"{Path(syntax).stem}.sublime-settings"
        return get_envs(settings_name)

    def is_visible(self, dirs: List[str] = None):
        # if not called from 'Side Bar.sublime-menu'
        if dirs is None:
            return True

        # only one directory selected
        return len(dirs) == 1

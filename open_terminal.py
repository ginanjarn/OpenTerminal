"""open terminal"""

import os
import subprocess
from pathlib import Path
from typing import Optional, List

import sublime
import sublime_plugin

DEFAULT_TERMINAL = ""
if os.name == "nt":
    DEFAULT_TERMINAL = "cmd.exe"
else:
    DEFAULT_TERMINAL = "gnome-terminal"


def get_workspace_folder(view: sublime.View) -> Optional[Path]:
    file_name = view.file_name()
    if not file_name:
        return None

    folders = view.window().folders()
    including_folder = [f for f in folders if view.file_name().startswith(f)]
    if including_folder:
        return Path(max(including_folder))

    return Path(file_name).parent


class OpenTerminalCommand(sublime_plugin.WindowCommand):
    def run(
        self,
        path: str = "",
        settings_name="",
        *,
        # next argument is defined in 'Side Bar.sublime-menu'
        paths: List[str] = None,
    ):
        # Load priority
        # 1. sidebar menu
        if paths:
            path = Path(paths[0])
        # 2. defined path
        elif path:
            path = Path(path)
        # 3. active view
        elif folder := get_workspace_folder(self.window.active_view()):
            path = Path(folder)
        else:
            path = Path().home()

        # Ensure if the path is directory or 'NotADirectoryError' will be raised
        if path.is_file():
            path = path.parent
        elif not path.exists():
            path = Path().home()

        self.open_terminal(path, settings_name)

    def open_terminal(self, path: Path, settings_name: str = ""):
        settings_name = settings_name or "Terminal.sublime-settings"
        settings = sublime.load_settings(settings_name)

        emulator = settings.get("emulator") or DEFAULT_TERMINAL
        envs = settings.get("envs") or None

        subprocess.Popen([emulator], cwd=path, env=envs)

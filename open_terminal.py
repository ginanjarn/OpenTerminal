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
    candidates = [f for f in folders if file_name.startswith(f)]
    if candidates:
        return Path(max(candidates))

    return Path(file_name).parent


EnvironType = dict


def environ_update(old: EnvironType, new: EnvironType) -> EnvironType:
    """"""
    if not new:
        return old

    temp = dict(old)
    os_path = os.pathsep.join([old["PATH"], new["PATH"]])
    temp.update(new)
    temp["PATH"] = os_path
    return temp


class OpenTerminalCommand(sublime_plugin.WindowCommand):
    def run(
        self,
        path: str = "",
        settings_name: str = "",
        # call from 'Side Bar.sublime-menu'
        dirs: List[str] = None,
    ):
        # Load priority
        # 1. defined path
        if path:
            path = Path(path)

        # 2. sidebar menu
        elif dirs:
            path = Path(dirs[0])

        # 3. active view
        elif folder := get_workspace_folder(self.window.active_view()):
            path = Path(folder)

        # default open user home directory
        else:
            path = Path().home()

        # Ensure if the path is directory or 'NotADirectoryError' will be raised
        if not path.is_dir():
            print(f"'{path!s}' is not a directory!")
            return

        self.open_terminal(path, settings_name)

    def open_terminal(self, path: Path, settings_name: str = ""):
        settings_name = settings_name or "Terminal.sublime-settings"
        settings = sublime.load_settings(settings_name)

        emulator = settings.get("emulator") or DEFAULT_TERMINAL
        settings_envs = settings.get("envs") or None
        # update current system environment
        envs = environ_update(os.environ, settings_envs)

        try:
            subprocess.Popen([emulator], cwd=path, env=envs)
        except Exception:
            print(
                f"Error open '{emulator!s}'."
                " Please set the terminal emulator in settings."
            )

    def is_visible(self, dirs: List[str] = None):
        # if not called from 'Side Bar.sublime-menu'
        if dirs is None:
            return True

        # only one directory selected
        return len(dirs) == 1

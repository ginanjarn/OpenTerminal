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
        arguments = settings.get("arguments") or ""
        # update current system environment
        envs = environ_update(os.environ, settings_envs)

        try:
            command = [emulator] + shlex.split(arguments)
            subprocess.Popen(command, cwd=path, env=envs)
        except Exception:
            print(f"Error open terminal : {shlex.join(command)!r}")
            sublime.error_message(
                "Error open terminal emulator!\n"
                "\n"
                "From menu 'Preferences' >"
                " 'Package Settings' > 'Terminal' > 'Settings'\n"
                "\n"
                "Set the 'emulator' property with your prefered emulator."
            )

    def is_visible(self, dirs: List[str] = None):
        # if not called from 'Side Bar.sublime-menu'
        if dirs is None:
            return True

        # only one directory selected
        return len(dirs) == 1

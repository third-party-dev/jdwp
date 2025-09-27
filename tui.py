#!/usr/bin/env python3


from textual.app import App, ComposeResult
from textual.events import Key, Click
from textual.widgets import Button, Header, Label, Static, Footer, Input, TextArea
from textual.widgets import Header, Static, Footer, TextArea
from textual.containers import Horizontal, VerticalScroll, Vertical
from textual.binding import Binding
from rich.text import Text
import shlex

from thirdparty.jdwp.tui.cmdinput import CmdInput
from thirdparty.jdwp.tui.adb import AdbCommand


class MyCmdInput(CmdInput):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Register adb as a command
        self.adb_command = AdbCommand(self)


    def get_prompt(self):
        '''Implemented as a method for dynamic behaviors.'''
        return '> '


    def cmd_log(self, out):
        self.cmd_scroll.mount(Static(out), before=self)
        self.cmd_scroll.scroll_end(animate=False)


    def process_cmd(self, cmd):
        self.cmd_log(f"{self.last_prompt}{cmd}")

        # Split command for argparse processing.
        args = shlex.split(cmd)
        if len(args) < 1:
            return

        if args[0] == 'clear':
            self.cmd_scroll.remove_children(Static)
            self.cmd_scroll.mount(self)
            return

        # Deal with application specific command.
        if args[0] == 'adb':
            self.cmd_scroll.mount(Static(self.adb_command.handle(args)), before=self)
            return
        
        self.cmd_scroll.mount(Static("Command not recognized."), before=self)


    def on_mount(self) -> None:
        # Fetch the reference to this once.
        self.cmd_scroll = self.app.query_one("#cmd_scroll")


class CodeLine(Static):

    def on_click(self, event: Click) -> None:
        event.stop()
        event.prevent_default()

        watch = self.app.query_one("#watch_scroll")
        watch.mount(Static(f"{self.meta}"))


class MyApp(App):
    
    TITLE = "Debugger"


    CSS = """
        Screen {
            layout: vertical;
        }

        #code_title, #watch_title, #cmd_title {
            height: 1;
            background: $primary;
            color: black;
            content-align: center middle;
        }

        #history {
            background: black;
            color: white;
        }

        #watch_frame, #code_frame {
            height: 1fr;
            border: solid blue;
        }

        #cmd_frame {
          background: black;
          height: 1fr;
          border: solid blue;
        }

        #cmd_input {
          background: black;
          border: none;
          padding: 0;
          margin: 0;
          height: 4;
        }
    """


    BINDINGS = [
        Binding("escape", "focus_cmd_input", "Command Input"),
    ]


    def __init__(self, **kwargs):
        super().__init__(**kwargs)


    def compose(self) -> ComposeResult:

        yield Header()
        with Vertical():
            yield Static("Key Bindings Here", id="keybinding_header")
            with Vertical(id="code_frame"):
                yield Static("Code View", id="code_title")
                yield VerticalScroll(id="code_scroll")
                #yield Static(''.join(code_lines), id="code_content")
            with Vertical(id="watch_frame"):
                yield Static("Watch View", id="watch_title")
                with VerticalScroll(id="watch_scroll"):
                    yield Static("JSON or Python Print Content Here", id="watch_content")
            with Vertical(id="cmd_frame"):
                yield Static("Command View", id="cmd_title")
                with VerticalScroll(id="cmd_scroll"):
                    yield MyCmdInput(id="cmd_input", soft_wrap=True)
        yield Footer()


    def on_mount(self) -> None:

        # Grab references to all of these once.
        self.code_scroll = self.query_one("#code_scroll")
        self.watch_scroll = self.query_one("#watch_scroll")
        self.cmd_scroll = self.query_one("#cmd_scroll")
        self.cmd_input = self.query_one("#cmd_input")

        # Application specific, but this is where we "list objects."
        self.load_file('/etc/passwd')
        self.code_scroll.mount_all(self.code_lines)
        self.cmd_input.focus()

    
    def load_file(self, fpath):
        self.code_content = {}
        self.code_lines = []
        with open(fpath, "r") as f:
            idx = 0
            for line in f.readlines():
                self.code_content[idx] = {
                    'content': line,
                    'index': idx,
                }
                code_line = CodeLine(line)
                code_line.meta = self.code_content[idx]
                self.code_lines.append(code_line)
        
    
    def action_focus_cmd_input(self) -> None:
        self.cmd_input.focus()


    def watch_log(self, out):
        self.watch_scroll.mount(Static(out))
        self.watch_scroll.scroll_end(animate=False)



if __name__ == "__main__":
    MyApp().run()
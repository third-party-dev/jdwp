#!/usr/bin/env python3

'''
This has become a bit of a bullshit nightmare. Textual has much better visuals and
mouse support. Prompt_toolkit has much better REPL support. Essentially, they are
both really shitty at what they don't do and I need both of those things.

Textualize, atm, seems like the way to go and I'll need to re-implement the aspects
of prompt_toolkit that don't exist. This includes a "ok" REPL interface. As a minimal
viable thing, this seems very doable as long as i catch all the weird edge cases with
Text Areas.

The more complex aspect of this is the "code browser". Here, I want to display thousands
of entries in a list. I had hoped that Textualize or Prompt_Toolkit could handle the
optimizations of this, but it doesn't appear to do so. The implementation vision is:

- Have an authoratative database (i.e. dict) that stores everything. The code editor itself
will need to dynamically generate Static lines for each of the database entries as they
become close to being viewed. (For now we'll play it naive and have Static for everything
always.)
- Each Static should be able to handle click/tap events that provide more information
  or allow setting breakpoints, etc.
- Each Static will have its own style so that it'll have a different color scheme when
  its a breakpoint or active instruction pointer (or other important status.)
- We also want to be able to inject comment Static that are not part of the original code.l
'''



import asyncio

from textual import events
from textual.app import App, ComposeResult
from textual.events import Key
from textual.widgets import Button, Header, Label, Static, Footer, Input, TextArea
from textual.containers import Horizontal, VerticalScroll, Vertical
from textual.binding import Binding
from textual.message import Message
from rich.text import Text
from rich.console import Console
from rich.syntax import Syntax
import datetime
import json
import math
from textual.events import Key
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.document import Document
from textual import work

class CmdInput(TextArea):

    def get_prompt(self):
        return self.prompt


    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if 'prompt' not in kwargs:
            self.prompt = '> '
        else:
            self.prompt = kwargs['prompt']


    def on_mount(self) -> None:
        self.insert(self.get_prompt())


    def process_cmd(self, cmd):
        vscroll = self.app.query_one("#cmd_scroll")
        pass
    

    def on_key(self, event: Key) -> None:
        if event.key == "enter":
            vscroll = self.app.query_one("#cmd_scroll")
            
            # TODO: We need the length of the previous prompt?!
            prompt_length = len(self.get_prompt())

            cmd_input = self.app.query_one("#cmd_input")
            cmd = cmd_input.text[prompt_length:]
            vscroll.mount(Static(f"{cmd_input.text}"), before=self)
            vscroll.scroll_end(animate=False)
            event.stop()
            event.prevent_default()
            self.clear()
            self.insert(self.get_prompt())

            self.process_cmd(cmd)


class MyApp(App):
    
    TITLE = "Mine"


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

        #code_frame, #watch_frame, #cmd_frame {
            height: 1fr;
            border: solid blue;
        }

        #cmd_input {
          border: none;
          padding: 0;
          margin: 0;
        }
    """

    BINDINGS = [
        Binding("escape", "focus_cmd_input", "Command Input"),
    ]

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
                    yield CmdInput(id="cmd_input")
        yield Footer()
    

    def on_mount(self) -> None:

        self.load_file('/etc/passwd')
        self.query_one("#code_scroll").mount_all(self.code_lines)
        self.query_one("#cmd_input").focus()
        
    
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
                self.code_lines.append(Static(line))
        
    
    def action_focus_cmd_input(self) -> None:
        self.query_one("#cmd_input").focus


if __name__ == "__main__":
    MyApp().run()
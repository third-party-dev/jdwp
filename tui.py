#!/usr/bin/env python3

import asyncio

from textual.app import App, ComposeResult
from textual.events import Key
from textual.widgets import Button, Header, Label, Static, Footer, Input
from textual.containers import Horizontal, VerticalScroll, Vertical
from textual.binding import Binding
from textual.message import Message
from rich.text import Text
from rich.console import Console
from rich.syntax import Syntax
import datetime
import json
import math


class REPLLine(Static):
    """A single line in the REPL output."""
    
    def __init__(self, content: str, line_type: str = "output", **kwargs):
        super().__init__(**kwargs)
        self.line_type = line_type
        self.content = content
    
    def on_mount(self) -> None:
        if self.line_type == "prompt":
            # Input prompt styling
            self.update(f"[bold green]>>>[/bold green] {self.content}")
        elif self.line_type == "output":
            # Regular output
            self.update(self.content)
        elif self.line_type == "error":
            # Error output in red
            self.update(f"[red]{self.content}[/red]")
        elif self.line_type == "success":
            # Success output in green
            self.update(f"[green]{self.content}[/green]")
        elif self.line_type == "info":
            # Info output in blue
            self.update(f"[blue]{self.content}[/blue]")

class REPLView(VerticalScroll):
    """A REPL-like scrollable view."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.command_history = []
        self.history_index = -1
        self.variables = {}  # Store variables for the REPL session
    
    def compose(self) -> ComposeResult:
        yield REPLLine("Welcome to the REPL interface!", "info")
        yield REPLLine("Type 'help' for available commands.", "info")
        yield REPLLine("", "output")
    
    def add_line(self, content: str, line_type: str = "output") -> None:
        """Add a new line to the REPL view."""
        line = REPLLine(content, line_type)
        self.mount(line)
        # Auto-scroll to bottom
        self.scroll_end()
    
    def execute_command(self, command: str) -> None:
        """Execute a command and display the result."""
        # Add the command to history
        if command.strip():
            self.command_history.append(command)
            self.history_index = len(self.command_history)
        
        # Display the command
        self.add_line(command, "prompt")
        
        # Parse and execute the command
        result = self.process_command(command.strip())
        
        # Display the result
        if result:
            self.add_line(result["content"], result["type"])
        
        # Add empty line for spacing
        self.add_line("", "output")
    
    def process_command(self, command: str) -> dict:
        """Process a command and return the result."""
        if not command:
            return None
        
        # Built-in commands
        if command == "help":
            help_text = """Available commands:
• help - Show this help message
• clear - Clear the REPL view
• history - Show command history
• vars - Show stored variables
• set <var> <value> - Set a variable
• get <var> - Get a variable value
• calc <expression> - Calculate math expression
• time - Show current time
• echo <text> - Echo text back
• json <data> - Pretty print JSON
• exit - Exit the application"""
            return {"content": help_text, "type": "info"}
        
        elif command == "clear":
            # Clear all children except keep the welcome messages
            for child in list(self.children):
                child.remove()
            self.mount(REPLLine("REPL cleared.", "success"))
            return None
        
        elif command == "history":
            if not self.command_history:
                return {"content": "No command history.", "type": "info"}
            history_text = "\n".join([f"{i+1}. {cmd}" for i, cmd in enumerate(self.command_history[-10:])])  # Last 10 commands
            return {"content": f"Recent commands:\n{history_text}", "type": "info"}
        
        elif command == "vars":
            if not self.variables:
                return {"content": "No variables stored.", "type": "info"}
            vars_text = "\n".join([f"{k} = {v}" for k, v in self.variables.items()])
            return {"content": f"Stored variables:\n{vars_text}", "type": "info"}
        
        elif command == "time":
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return {"content": f"Current time: {current_time}", "type": "info"}
        
        elif command == "exit":
            self.app.exit()
            return None
        
        # Commands with arguments
        elif command.startswith("set "):
            parts = command.split(" ", 2)
            if len(parts) >= 3:
                var_name = parts[1]
                var_value = parts[2]
                # Try to parse as different types
                try:
                    if var_value.lower() in ["true", "false"]:
                        self.variables[var_name] = var_value.lower() == "true"
                    elif var_value.isdigit() or (var_value.startswith("-") and var_value[1:].isdigit()):
                        self.variables[var_name] = int(var_value)
                    elif "." in var_value and all(c.isdigit() or c in ".-" for c in var_value):
                        self.variables[var_name] = float(var_value)
                    else:
                        self.variables[var_name] = var_value
                    return {"content": f"Variable '{var_name}' set to: {self.variables[var_name]}", "type": "success"}
                except ValueError:
                    self.variables[var_name] = var_value
                    return {"content": f"Variable '{var_name}' set to: {var_value}", "type": "success"}
            else:
                return {"content": "Usage: set <variable> <value>", "type": "error"}
        
        elif command.startswith("get "):
            var_name = command[4:].strip()
            if var_name in self.variables:
                return {"content": f"{var_name} = {self.variables[var_name]}", "type": "success"}
            else:
                return {"content": f"Variable '{var_name}' not found.", "type": "error"}
        
        elif command.startswith("echo "):
            echo_text = command[5:]
            return {"content": echo_text, "type": "output"}
        
        elif command.startswith("calc "):
            expression = command[5:].strip()
            try:
                # Safe evaluation of math expressions
                allowed_names = {
                    k: v for k, v in math.__dict__.items() if not k.startswith("__")
                }
                allowed_names.update({"abs": abs, "round": round, "min": min, "max": max})
                # Add stored variables to the calculation context
                allowed_names.update(self.variables)
                
                result = eval(expression, {"__builtins__": {}}, allowed_names)
                return {"content": f"{expression} = {result}", "type": "success"}
            except Exception as e:
                return {"content": f"Calculation error: {str(e)}", "type": "error"}
        
        elif command.startswith("json "):
            json_text = command[5:].strip()
            try:
                # Try to parse as JSON
                data = json.loads(json_text)
                formatted = json.dumps(data, indent=2)
                return {"content": formatted, "type": "output"}
            except json.JSONDecodeError as e:
                return {"content": f"Invalid JSON: {str(e)}", "type": "error"}
        
        # Default: unknown command
        return {"content": f"Unknown command: {command}", "type": "error"}
    
    def get_history_command(self, direction: int) -> str:
        """Get a command from history. direction: -1 for previous, 1 for next."""
        if not self.command_history:
            return ""
        
        self.history_index += direction
        self.history_index = max(-1, min(self.history_index, len(self.command_history) - 1))
        
        if self.history_index == -1:
            return ""
        return self.command_history[self.history_index]

class ReplInput(Input):
    """Custom input widget with history navigation."""
    
    class CommandSubmitted(Message):
        """Message sent when a command is submitted."""
        
        def __init__(self, command: str) -> None:
            self.command = command
            super().__init__()
    
    def __init__(self, **kwargs):
        super().__init__(placeholder="Enter command...", **kwargs)
    
    def on_key(self, event) -> None:
        """Handle key events for history navigation."""
        repl_view = self.app.query_one("#repl-view", REPLView)
        
        if event.key == "up":
            # Previous command in history
            cmd = repl_view.get_history_command(-1)
            if cmd:
                self.value = cmd
                self.cursor_position = len(cmd)
            event.prevent_default()
        elif event.key == "down":
            # Next command in history
            cmd = repl_view.get_history_command(1)
            self.value = cmd
            self.cursor_position = len(cmd)
            event.prevent_default()
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle command submission."""
        command = event.value.strip()
        self.value = ""  # Clear input
        self.post_message(self.CommandSubmitted(command))


class MyApp(App):
    
    TITLE = "Mine"


    CSS = """
    Screen {
        layout: vertical;
    }

    #main {
        layout: vertical;
        height: 1fr;
    }

    #keybinding_header {
        height: 1;
        background: $primary;
        color: black;
        content-align: center middle;
    }

    #view_header {
        height: 1;
        background: $primary;
        color: black;
        content-align: center middle;
    }

    #row1 {
        height: 1fr;
    }
    #row1 Static {
        width: 1fr;
        border: solid green;
        content-align: center middle;
    }

    #code_view, #watch_view, #cli_view {
        height: 1fr;
        border: solid blue;
        /* content-align: center middle; */
    }



    #repl-container {
        height: 1fr;
        /*border: solid $primary;*/
        /*margin: 1;*/
    }

    #input-container {
        height: 3;
        /*padding: 1;*/
        /* background: $surface; */
        /* border: solid $primary;*/
        /*margin: 0 1 1 1; */
    }
    
    #repl-view {
        /*height: 1fr;*/
        padding: 1;
    }
    
    REPLLine {
        height: auto;
        margin-bottom: 0;
        padding: 0;
    }
    
    
    
    #repl-input {
        width: 1fr;
    }
    
    #prompt-label {
        height: 3;
        width: auto;
        margin-bottom: 1;
        color: white;
        /* color: $text; */
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
        Binding("ctrl+l", "clear_repl", "Clear REPL"),
        Binding("escape", "focus_input", "Focus Input"),
    ]

    def compose(self) -> ComposeResult:
        with open("/etc/passwd", "r") as f:
            etc_passwd = f.read()

        yield Header()

        with Vertical():
            yield Static("Key Bindings Here", id="keybinding_header")
            with Vertical(id="code_view"):
                yield Static("Code View", id="view_header")
                with VerticalScroll():
                    yield Static(etc_passwd)
            with Vertical(id="watch_view"):
                yield Static("Watch View", id="view_header")
                with VerticalScroll():
                    yield Static("JSON or Python Print Content Here")
            with Vertical(id="cli_view"):
                yield Static("CLI View", id="view_header")

                with VerticalScroll(id="repl-container"):
                    yield REPLView(id="repl-view")
                
                with Horizontal(id="input-container"):
                    yield Static("\nREPL> ", id="prompt-label")
                    yield ReplInput(id="repl-input")


        yield Footer()
    

    #def on_key(self, event: Key):
    #    self.title = event.key
    #    self.sub_title = f"You just pressed {event.key}!"
    

    def on_mount(self) -> None:
        # Focus the input by default
        #obj = self.query_one("#repl-input")
        self.query_one("#repl-input").view = self.query_one("#repl-view")
        self.query_one("#repl-input").focus()
    
    def on_repl_input_command_submitted(self, message: ReplInput.CommandSubmitted) -> None:
        self.query_one("#repl-view").mount(REPLLine(f"Another info line.", "info"))
        repl_view = self.query_one("#repl-view", REPLView)
        repl_view.execute_command(message.command)
    
    def action_clear_repl(self) -> None:
        repl_view = self.query_one("#repl-view", REPLView)
        repl_view.execute_command("clear")
    
    def action_focus_input(self) -> None:
        self.query_one("#repl-input").focus()


if __name__ == "__main__":
    app = MyApp()
    app.run()
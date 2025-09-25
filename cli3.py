from prompt_toolkit import Application
from prompt_toolkit.layout import Layout, HSplit, Window
from prompt_toolkit.widgets import TextArea, Frame
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.dimension import Dimension

from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory


class OutputArea(TextArea):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def log(self, entry):
        buf = self.buffer
        # Move cursor to end
        buf.cursor_position = len(buf.text)
        # Append the new line
        if not buf.text.endswith("\n"):
            buf.insert_text("\n")
        buf.insert_text(entry + "\n")

    def scroll_to_line(self, line_index, app):
        ri = self.window.render_info
        if ri is None:
            return  # not rendered yet
        window_height = ri.window_height
        # Compute top line to scroll so line_index is centered
        new_scroll = max(0, line_index - window_height // 2)
        self.vertical_scroll = new_scroll
        app.invalidate()

class SingleTextAreaApp:
    def __init__(self):
        # Create ONE TextArea that handles everything
        with open("/etc/passwd", "r") as f:
            code_data = f.read()
        self.code_area = OutputArea(
            text=code_data,
            multiline=True,
            scrollbar=True,
            wrap_lines=True,
            #height=Dimension(weight=1),
        )

        self.watch_area = OutputArea(
            text="Watch goes here.",
            multiline=True,
            scrollbar=True,
            wrap_lines=True,
            height=10,
        )

        # Create ONE TextArea that handles everything
        self.cli_area = TextArea(
            text="Welcome to the application!\nType 'help' for available commands.\n> ",
            multiline=True,
            scrollbar=True,
            wrap_lines=True,
            height=10,
        )

        # Create layout
        code_frame = Frame(self.code_area, title="Code")
        watch_frame = Frame(self.watch_area, title="Watch")
        cli_frame = Frame(self.cli_area, title="CLI")
        
        # Combine into layout
        container = HSplit([
            code_frame,
            watch_frame,
            cli_frame,
        ])
    

        self.layout = Layout(container, focused_element=self.cli_area)
        
        # Position cursor at the end
        self.cli_area.buffer.cursor_position = len(self.cli_area.text)
        
        # Create application with ONLY the text area
        self.app = Application(
            layout=self.layout,
            key_bindings=self.create_key_bindings(),
            full_screen=True,
            mouse_support=True,
        )

    def code_log(self, line: str):
        buf = self.code_area.buffer
        # Move cursor to end
        buf.cursor_position = len(buf.text)
        # Append the new line
        if not buf.text.endswith("\n"):
            buf.insert_text("\n")
        buf.insert_text(line + "\n")
    
    def create_key_bindings(self):
        kb = KeyBindings()
        
        @kb.add('c-q')
        def quit_app(event):
            event.app.exit()
        
        @kb.add('enter')
        def handle_enter(event):
            # Get all text
            text = self.cli_area.text
            cursor = self.cli_area.buffer.cursor_position
            
            # Find the current line
            lines = text[:cursor].split('\n')
            current_line = lines[-1]
            
            # If we're on a prompt line, execute command
            if current_line.startswith('> '):
                command = current_line[2:].strip()
                
                # Move to end and add newline
                self.cli_area.buffer.cursor_position = len(self.cli_area.text)
                self.cli_area.buffer.insert_text('\n')
                
                if command:
                    self.execute_command(command)
                
                # Add new prompt
                self.cli_area.buffer.insert_text('> ')
            else:
                # Normal newline
                self.cli_area.buffer.insert_text('\n')

        # Don't allow removing prompt.
        @kb.add("backspace")
        def _(event):
            PROMPT_LENGTH = 2
            doc = self.cli_area.buffer.document
            if doc.cursor_position_col > PROMPT_LENGTH:
                #self.code_log(f"{doc.cursor_position_col}")
                self.cli_area.buffer.delete_before_cursor(1)
            else:
                # ignore backspace if at prompt
                pass

        # Don't allow going into output.
        @kb.add("up")
        def _(event):
            buf = self.cli_area.buffer
            doc = buf.document
            if doc.cursor_position_row < doc.line_count - 1:
                buf.cursor_up(count=1)

        
        return kb

    
    def execute_command(self, command):
        parts = command.split()
        if not parts:
            return
        
        cmd = parts[0].lower()
        
        if cmd == 'help':
            self.cli_area.buffer.insert_text("Available commands:\n- help\n- echo <text>\n")
        
        elif cmd == 'scroll':
            self.watch_area.log("We be here.")
            self.code_area.buffer.cursor_position = 30
            #self.code_area.window.focus()
            #self.code_area.window.vertical_scroll += 5
            #self.app.invalidate()
            #self.cli_area.window.focus()
            #scroll_to_line(23, self.app)

        elif cmd == 'echo':
            if len(parts) > 1:
                text = ' '.join(parts[1:])
                self.cli_area.buffer.insert_text(f"Echo: {text}\n")
            else:
                self.cli_area.buffer.insert_text("Echo: (no text)\n")
        
        else:
            self.cli_area.buffer.insert_text(f"Unknown command: {cmd}\n")
    
    def run(self):
        self.app.run()

def main():
    app = SingleTextAreaApp()
    app.run()

if __name__ == "__main__":
    main()
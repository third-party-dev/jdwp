'''
Copyright (c) 2025 Vincent Agriesti

This file is part of the thirdparty JDWP project.
Licensed under the MIT License. See the LICENSE file in the project root
for full license text.
'''

from textual.events import Key
from textual.widgets import TextArea
from textual.binding import Binding


class CmdInput(TextArea):

    BINDINGS = [
        Binding("up", "move_event('up')", "Up", show=False),
        Binding("shift+up", "move_event('shift+up')", "_", show=False),

        Binding("left", "move_event('left')", "_", show=False),
        Binding("shift+left", "move_event('shift+left')", "_", show=False),

        Binding("ctrl+left", "move_event('ctrl+left')", "_", show=False),
        Binding("ctrl+shift+left", "move_event('ctrl+shift+left')", "_", show=False),

        Binding("home,ctrl+a", "move_event('home')", "_", show=False),
        Binding("shift+home", "move_event('shift+home')", "_", show=False),

        Binding("f6", "move_event('f6')", "_", show=False),
        Binding("f7", "move_event('f7')", "_", show=False),

        Binding("pageup", "move_event('pageup')", "_", show=False),
        Binding("shift+pageup", "move_event('shift+pageup')", "_", show=False),

        Binding("backspace", "del_event('backspace')", "_", show=False),
        Binding("ctrl+w", "del_event('ctrl+w')", "_", show=False),
        Binding("ctrl+u", "del_event('ctrl+u')", "_", show=False),
        Binding("ctrl+shift+k", "del_event('ctrl+shift+k')", "_", show=False),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    def get_prompt(self):
        '''Implemented as a method for dynamic behaviors.'''
        return '> '


    def display_prompt(self):
        self.clear()
        prompt = self.get_prompt()
        self.last_prompt = prompt
        self.last_prompt_length = len(prompt)
        self.insert(prompt)


    def on_mount(self) -> None:
        self.display_prompt()


    def process_cmd(self, cmd):
        raise NotImplemented("Error: process_cmd method not implemented in base class.")


    def action_move_event(self, key):
        if key in ['home', 'ctrl+a', 'shift+home']:
            self.action_cursor_line_start('shift' in key)
        elif key in ['up', 'shift+up']:
            self.action_cursor_up('shift' in key)
        elif key in ['left', 'shift+left']:
            self.action_cursor_left('shift' in key)
        elif key in ['ctrl+left', 'ctrl+shift+left']:
            self.action_cursor_word_left('shift' in key)
        elif key in ['pageup', 'shift+pageup']:
            self.action_cursor_page_up('shift' in key)
        elif key == 'f6':
            self.action_select_line()
        elif key == 'f7':
            self.action_select_all()

        selected = not self.selection.is_empty
        selection = {
            'start': self.selection.start,
            'end': self.selection.end,
        }
        
        if selected:
            if selection['start'][0] == 0 and selection['start'][1] < self.last_prompt_length:
                selection['start'] = (0, self.last_prompt_length)
            if selection['end'][0] == 0 and selection['end'][1] < self.last_prompt_length:
                selection['end'] = (0, self.last_prompt_length)
            # Note: shift+home then right will jump to end of select as a textual behavior,
            #       not a behavior of this code.
            self.move_cursor(selection['start'], select=False)
            self.move_cursor(selection['end'], select=True)
        else:    
            (row, col) = self.cursor_location
            if row == 0 and col <= self.last_prompt_length:
                self.move_cursor((0, self.last_prompt_length), select=False)


    def action_del_event(self, key):
        if key == 'backspace':
            self.action_delete_left()
        if key == 'ctrl+w':
            self.action_delete_word_left()
        if key == 'ctrl+u':
            self.action_delete_to_start_of_line()
        if key == 'ctrl+shift+k':
            # Note: Tested, but has not been confirmed working yet.
            self.action_delete_line()

        (row, col) = self.cursor_location
        if row == 0 and col < self.last_prompt_length:
            self.insert(self.last_prompt[col:self.last_prompt_length])

    
    def on_key(self, event: Key) -> None:
        if event.key == "enter":
            # Fetch the command entered.
            cmd = self.text[self.last_prompt_length:]
            self.process_cmd(cmd)

            # Stop TextArea from getting Enter key event.
            event.stop()
            event.prevent_default()
            
            self.display_prompt()
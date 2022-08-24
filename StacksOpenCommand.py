import sublime
import sublime_plugin
from typing import Optional, List, Any, Dict
import json
import os
from Stacks.components.Common import _get_window_state, _stack_file_name, _close_open_views, _loaded_stack_name_settings_key
from Stacks.StacksCommand import StacksCommand
from Stacks.components.FileUtils import LoadError, load_stack_file
from Stacks.components.ResultTypes import Either, RightEither, LeftEither

class StacksOpenCommand(StacksCommand):

  def on_run(self, window: sublime.Window, stack_file: str):
    load_result: Either[LoadError, Dict[str, Any]] = load_stack_file(stack_file)

    if load_result.has_value():
      loaded_stacks = load_result.value()
      items: List[str] = [key for key in loaded_stacks.keys()]

      window.show_quick_panel(
        items = items,
        placeholder = "Which stack would you like to load?",
        on_select = lambda index: self.on_stack_load(stack_file, window, loaded_stacks, items, index)
      )
    else:
      error: LoadError = load_result.error()

      if error == LoadError.STACK_FILE_NOT_FOUND:
        sublime.message_dialog(f"Could not find saved file:\n{stack_file}.\nPlease try saving a stack first.")
      elif error == LoadError.COULD_NOT_DECODE_STACK_FILE:
        sublime.message_dialog(f"Could not decode {stack_file}.\nConsider deleting it and resaving it or make it a valid json file.")
      else:
        sublime.message_dialog(f"An unexpected error occurred: {error}")


  def on_stack_load(self, stack_file: str, window: sublime.Window, loaded_stacks: Dict[str, Any], stack_names: List[str], stack_index: int) -> None:
    if stack_index < 0 or stack_index > len(stack_names):
      return

    stack_name = stack_names[stack_index]

    # TODO: Validate stack_name
    has_stack_name_in_file = stack_name in loaded_stacks
    if has_stack_name_in_file:
      window_state: Dict[str, Any] = loaded_stacks[stack_name]

      _close_open_views(window)
      window.set_layout(window_state['layout'])

      # TODO make this safer or use a regex
      key_groups: List[int] = [int(key.split("group")[1]) for key in window_state.keys() if key.startswith("group")]

      for group in key_groups:
        views_in_group = window_state[f"group{group}"]
        for v in views_in_group:
          # TODO: Check if the file still exists
          window.open_file(fname = v, group = group)

      window.settings().update({_loaded_stack_name_settings_key : stack_name})
      print(f"stack loaded: {stack_name}")
    else:
      sublime.message_dialog(f"Could not find stack named:\n{stack_name}\nin:\n{stack_file}")

from glue.config import viewer_tool
from glue.utils.qt import pick_item
from glue.viewers.common.tool import Tool, SimpleToolMenu

__all__ = ['MoveTabTool']


@viewer_tool
class WindowTool(SimpleToolMenu):
    """
    A generic "window operations" tool that the Qt app and plugins
    can register tools for windowing operations with.
    """

    tool_id = 'window'
    icon = 'glue_move_x'
    tool_tip = 'Modify the viewer window'


@viewer_tool
class MoveTabTool(Tool):

    icon = 'glue_move_x'
    tool_id = 'window:movetab'
    action_text = 'Move to another tab'
    tool_tip = 'Move viewer to another tab'

    def activate(self):
        app = self.viewer.session.application
        tab = pick_item(range(app.tab_count), app.tab_names, title="Move Viewer", label="Select a tab")
        if tab is not None:
            app.move_viewer_to_tab(self.viewer, tab)

from glue.utils import defer_draw, decorate_all_methods
from glue.viewers.matplotlib.qt.data_viewer import MatplotlibDataViewer
from glue.viewers.scatter.qt.layer_style_editor import ScatterLayerStyleEditor
from glue.viewers.scatter.layer_artist import ScatterLayerArtist
from glue.viewers.scatter.qt.options_widget import ScatterOptionsWidget
from glue.viewers.scatter.state import ScatterViewerState

from glue.viewers.scatter.viewer import MatplotlibScatterMixin

from echo import add_callback
from qtpy.QtCore import Slot


__all__ = ['ScatterViewer']


@decorate_all_methods(defer_draw)
class ScatterViewer(MatplotlibScatterMixin, MatplotlibDataViewer):

    LABEL = '2D Scatter'
    _layer_style_widget_cls = ScatterLayerStyleEditor
    _state_cls = ScatterViewerState
    _options_cls = ScatterOptionsWidget
    _data_artist_cls = ScatterLayerArtist
    _subset_artist_cls = ScatterLayerArtist

    @Slot()
    def _on_toolbar_added(self):
        self._update_tools(self.state.plot_mode)

    tools = ['select:rectangle', 'select:xrange',
             'select:yrange', 'select:circle',
             'select:polygon']

    def __init__(self, session, parent=None, state=None):
        proj = None if not state or not state.plot_mode else state.plot_mode
        MatplotlibDataViewer.__init__(self, session, parent=parent, state=state, projection=proj)
        MatplotlibScatterMixin.setup_callbacks(self)

        self.toolbar_added.connect(self._on_toolbar_added)
        add_callback(self.state, 'plot_mode', self._on_plot_mode_update)

    def limits_to_mpl(self, *args):
        # These projections throw errors if we try to set the limits
        if self.state.plot_mode in ['aitoff', 'hammer', 'lambert', 'mollweide']:
            return
        super().limits_to_mpl(*args)

    def _update_tools(self, plot_mode):
        rectilinear = plot_mode == 'rectilinear'
        full_sphere = plot_mode in ['aitoff', 'hammer', 'lambert', 'mollweide']
        self.toolbar.tools['mpl:pan'].enabled = not full_sphere
        self.toolbar.tools['mpl:zoom'].enabled = rectilinear

    def _on_plot_mode_update(self, plot_mode):
        self._update_tools(plot_mode)

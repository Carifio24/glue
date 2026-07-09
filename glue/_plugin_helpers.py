# The following function is a thin wrapper around iter_entry_points. The reason it
# is in this separate file is that when making the Mac app, py2app doesn't
# support entry points, so we replace this function with a version that has the
# entry points we want hardcoded. If this function was in glue/main.py, the
# reference to the iter_plugin_entry_points function in load_plugin would be
# evaluated at compile time rather than at runtime, so the patched version
# wouldn't be used.

import os
import sys
import warnings
from collections import defaultdict

if sys.version_info >= (3, 10):
    from importlib.metadata import entry_points
else:
    from importlib_metadata import entry_points


REQUIRED_PLUGINS = ['glue.plugins.coordinate_helpers',
                    'glue.core.data_exporters',
                    'glue.io.formats.fits']


REQUIRED_PLUGINS_QT = ['glue_qt.plugins.tools.pv_slicer',
                       'glue_qt.viewers.image',
                       'glue_qt.viewers.scatter',
                       'glue_qt.viewers.histogram',
                       'glue_qt.viewers.profile',
                       'glue_qt.viewers.table']


def iter_plugin_entry_points():
    return iter(entry_points(group='glue.plugins'))


class PluginConfig(object):

    def __init__(self, plugins={}):
        self.plugins = defaultdict(lambda: True)
        self.plugins.update(plugins)

    def __str__(self):
        string = ""
        for plugin in sorted(self.plugins):
            string += "{0}: {1}\n".format(plugin, self.plugins[plugin])
        return string

    @classmethod
    def load(cls):

        # Import at runtime because some tests change this value. We also don't
        # just import the variable directly otherwise it is cached.
        from glue import config
        cfg_dir = config.CFG_DIR

        plugin_cfg = os.path.join(cfg_dir, 'plugins.cfg')

        import configparser

        config = configparser.ConfigParser()
        try:
            read = config.read(plugin_cfg)
        except configparser.Error as exc:
            # The file may have been corrupted by a previous non-atomic or
            # concurrent write and e.g. contain duplicate options. Fall back
            # to a tolerant parse (last occurrence of an option wins) rather
            # than failing - the file will be rewritten cleanly on the next
            # save().
            warnings.warn(f"Error while reading {plugin_cfg}:\n{exc}\n"
                          f"Falling back to parsing the file with "
                          f"strict=False.")
            config = configparser.ConfigParser(strict=False)
            read = config.read(plugin_cfg)

        if len(read) == 0 or not config.has_section('plugins'):
            return cls()

        plugins = {}
        for name, enabled in config.items('plugins'):
            plugins[name] = bool(int(enabled))

        self = cls(plugins=plugins)

        return self

    def save(self):

        # Import at runtime because some tests change this value. We also don't
        # just import the variable directly otherwise it is cached.
        from glue import config
        cfg_dir = config.CFG_DIR

        plugin_cfg = os.path.join(cfg_dir, 'plugins.cfg')

        # Don't rewrite the file when nothing has changed. In the common case
        # the config already lists every known plugin, so this avoids touching
        # disk on every startup and removes almost all of the opportunity for
        # concurrent processes to write the file at the same time.
        if dict(PluginConfig.load().plugins) == dict(self.plugins):
            return

        import configparser

        config = configparser.ConfigParser()
        config.add_section('plugins')

        for key in sorted(self.plugins):
            config.set('plugins', key, value=str(int(self.plugins[key])))

        os.makedirs(cfg_dir, exist_ok=True)

        # Write atomically: serialize to a uniquely-named temporary file in the
        # same directory and rename it into place. os.replace overwrites the
        # destination in a single step, so a concurrent reader (e.g. another
        # process during a parallel test run) always sees either the old or the
        # new file, never a partially-written or interleaved one.
        import tempfile
        fd, tmp_path = tempfile.mkstemp(dir=cfg_dir, prefix='plugins.cfg.',
                                        suffix='.tmp')
        try:
            with os.fdopen(fd, 'w') as fout:
                config.write(fout)
            try:
                os.replace(tmp_path, plugin_cfg)
            except OSError:
                # Windows refuses to rename over a file that another process
                # currently has open, unlike POSIX. That can only happen once a
                # valid file already exists (every write is a whole-file rename)
                # and the config is non-critical, so ignore it. A genuine
                # failure leaves no file in place and is re-raised.
                if not os.path.exists(plugin_cfg):
                    raise
        finally:
            # Remove the temporary file if the rename did not consume it (an
            # error, or an ignored Windows sharing conflict).
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

    def filter(self, keep):
        """
        Keep only certain plugins.

        This is used to filter out plugins that are not installed.
        """
        for key in list(self.plugins.keys())[:]:
            if key not in keep:
                self.plugins.pop(key)

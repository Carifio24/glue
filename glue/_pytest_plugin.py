"""A pytest plugin, registered through the ``pytest11`` entry point, that
isolates glue's configuration directory for the duration of a test run.

It is loaded automatically whenever glue is installed, and gives each pytest
process (including each pytest-xdist worker, which runs ``pytest_configure``
independently) its own throwaway config directory. As a result tests never read
from or write to the developer's real ``~/.glue``, and parallel workers never
share ``plugins.cfg`` and race while rewriting it.

Set ``glue_isolate_config = false`` in the pytest configuration to opt out, or
set ``PYTEST_DISABLE_PLUGIN_AUTOLOAD`` to disable autoloaded plugins entirely.
"""

import shutil
import tempfile


def pytest_addoption(parser):
    parser.addini('glue_isolate_config',
                  help='Redirect glue config dir to a temporary location during tests.',
                  type='bool', default=True)


def pytest_configure(config):
    if not config.getini('glue_isolate_config'):
        return

    from glue import config as glue_config

    # mkdtemp creates a uniquely-named directory, so each process (and each
    # xdist worker) gets its own without needing to consult the worker id.
    cfg_dir = tempfile.mkdtemp(prefix='glue-test-cfg-')
    config._glue_isolated_cfg_dir = cfg_dir
    glue_config.CFG_DIR = cfg_dir


def pytest_unconfigure(config):
    cfg_dir = getattr(config, '_glue_isolated_cfg_dir', None)
    if cfg_dir is not None:
        shutil.rmtree(cfg_dir, ignore_errors=True)

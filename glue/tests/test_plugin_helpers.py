import os
import configparser
from concurrent.futures import ThreadPoolExecutor

import pytest

from glue._plugin_helpers import PluginConfig


def test_config_dir_isolated_by_pytest_plugin(request):
    # The bundled pytest plugin (glue._pytest_plugin) redirects the config dir
    # to a per-process temporary location during tests, which is what keeps
    # parallel workers from sharing plugins.cfg. Skip only if it was disabled.
    if not request.config.getini('glue_isolate_config'):
        pytest.skip('glue config isolation disabled via glue_isolate_config')

    import glue.config
    assert os.path.basename(glue.config.CFG_DIR).startswith('glue-test-cfg-')


def test_save_load_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr('glue.config.CFG_DIR', str(tmp_path))

    PluginConfig(plugins={'plugin_a': True, 'plugin_b': False}).save()

    loaded = PluginConfig.load()
    assert loaded.plugins['plugin_a'] is True
    assert loaded.plugins['plugin_b'] is False


def test_save_leaves_no_temporary_files(tmp_path, monkeypatch):
    monkeypatch.setattr('glue.config.CFG_DIR', str(tmp_path))

    PluginConfig(plugins={'plugin_a': True}).save()

    assert os.listdir(tmp_path) == ['plugins.cfg']


def test_load_tolerates_duplicate_options(tmp_path, monkeypatch):
    # A file corrupted by a previous concurrent/non-atomic write can contain
    # the same option twice. Reading it should warn, not raise
    # DuplicateOptionError.
    monkeypatch.setattr('glue.config.CFG_DIR', str(tmp_path))

    (tmp_path / 'plugins.cfg').write_text(
        "[plugins]\ndendro_factory = 1\ndendro_factory = 1\n")

    with pytest.warns(UserWarning, match='Falling back to parsing the file'):
        loaded = PluginConfig.load()
    assert loaded.plugins['dendro_factory'] is True


def test_concurrent_save_and_load(tmp_path, monkeypatch):
    # Regression test: hammering save() from several threads while another
    # thread repeatedly loads must never expose a partially written or
    # duplicated config, because save() renames the file into place atomically.
    monkeypatch.setattr('glue.config.CFG_DIR', str(tmp_path))

    plugins = {'plugin_{0}'.format(i): True for i in range(50)}
    plugin_cfg = str(tmp_path / 'plugins.cfg')

    def writer():
        for _ in range(50):
            PluginConfig(plugins=plugins).save()

    def reader():
        # Parse strictly so that a torn or duplicated write raises instead of
        # being silently tolerated; the atomic save() must prevent that. A
        # missing file is fine (read() returns []), and on Windows an open that
        # races an atomic replace can be transiently denied, which is a sharing
        # artifact rather than config corruption, so ignore PermissionError.
        for _ in range(200):
            try:
                configparser.ConfigParser(strict=True).read(plugin_cfg)
            except PermissionError:
                pass

    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(writer) for _ in range(4)]
        futures += [executor.submit(reader) for _ in range(2)]
        for future in futures:
            future.result()

    assert os.listdir(tmp_path) == ['plugins.cfg']
    assert PluginConfig.load().plugins == plugins

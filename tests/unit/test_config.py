import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock


class TestConfigMigration:
    def test_config_uses_configparser(self):
        from plexpy.config import core
        assert hasattr(core, 'configparser')

    def test_config_class_init(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            f.write('[General]\n')
            f.write('date_format = YYYY-MM-DD\n')
            config_path = f.name

        try:
            from plexpy.config.core import Config
            config = Config(config_path)
            assert config.DATE_FORMAT == 'YYYY-MM-DD'
        finally:
            os.unlink(config_path)

    def test_config_get_setting(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            f.write('[General]\n')
            f.write('date_format = YYYY-MM-DD\n')
            config_path = f.name

        try:
            from plexpy.config.core import Config
            config = Config(config_path)
            value = config.get_setting('DATE_FORMAT')
            assert value == 'YYYY-MM-DD'
        finally:
            os.unlink(config_path)

    def test_config_set_setting(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            f.write('[General]\n')
            f.write('date_format = YYYY-MM-DD\n')
            config_path = f.name

        try:
            from plexpy.config.core import Config
            config = Config(config_path)
            config.DATE_FORMAT = 'YYYY/MM/DD'
            assert config.DATE_FORMAT == 'YYYY/MM/DD'
        finally:
            os.unlink(config_path)


class TestMigrationsSettings:
    def test_settings_uses_configparser(self):
        from plexpy.db.migrations import settings
        assert hasattr(settings, 'configparser')

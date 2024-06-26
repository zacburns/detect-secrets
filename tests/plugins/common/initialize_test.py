import mock
import pytest

from detect_secrets.plugins.common import initialize
from detect_secrets.plugins.high_entropy_strings import Base64HighEntropyString
from detect_secrets.plugins.high_entropy_strings import HexHighEntropyString


class TestFromPluginClassname:

    def test_success(self):
        plugin = initialize.from_plugin_classname(
            'HexHighEntropyString',
            hex_limit=4,
        )

        assert isinstance(plugin, HexHighEntropyString)
        assert plugin.entropy_limit == 4

    def test_return_none_if_not_base_plugin(self):
        plugin = initialize.from_plugin_classname(
            'log',
        )

        assert not plugin

    def test_fails_on_bad_initialization(self):
        with mock.patch.object(
            HexHighEntropyString,
            '__init__',
            side_effect=TypeError,
        ), pytest.raises(
            TypeError,
        ):
            initialize.from_plugin_classname(
                'HexHighEntropyString',
                hex_limit=4,
            )


class TestFromSecretType:

    def setup_method(self):
        self.settings = [
            {
                'name': 'Base64HighEntropyString',
                'base64_limit': 3,
            },
            {
                'name': 'PrivateKeyDetector',
            },
        ]

    def test_success(self):
        plugin = initialize.from_secret_type(
            'Base64 High Entropy String',
            settings=self.settings,
        )

        assert isinstance(plugin, Base64HighEntropyString)
        assert plugin.entropy_limit == 3

    def test_failure(self):
        assert not initialize.from_secret_type(
            'some random secret_type',
            settings=self.settings,
        )

    def test_secret_type_not_in_settings(self):
        assert not initialize.from_secret_type(
            'Base64 High Entropy String',
            settings=[],
        )

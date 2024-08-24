import pytest
from mkdocs.config import config_options

from mkdocs_argref_plugin.argref import AutoLinkOption


def test_missing_variable_in_target_url_sing():
    values = [
        {
            "reference_prefix": "GH-",
            "target_url": "http://gh/TAG-",
        },
    ]
    with pytest.raises(config_options.ValidationError) as exc_info:
        AutoLinkOption().run_validation(values)
    assert exc_info.value.args[0] == "All variables must be used in 'target_url'"


def test_missing_variable_in_target_url_multi():
    values = [
        {
            "reference_prefix": "GH-<num>-<version>",
            "target_url": "http://gh/TAG-<version>",
        },
    ]
    with pytest.raises(config_options.ValidationError) as exc_info:
        AutoLinkOption().run_validation(values)
    assert exc_info.value.args[0] == "All variables must be used in 'target_url'"


def test_variable_in_prefix_found_in_target_url_single():
    values = [
        {
            "reference_prefix": "GH-<num>",
            "target_url": "http://gh/TAG-<num>",
        },
    ]
    AutoLinkOption().run_validation(values)


def test_variable_in_prefix_found_in_target_url_single_multi():
    values = [
        {
            "reference_prefix": "GH-<num>-<version>",
            "target_url": "http://gh/TAG-<num>-<version>",
        },
    ]
    AutoLinkOption().run_validation(values)

import pytest

from argref.main import AutoLinkOption, replace_autolink_references as autolink

from mkdocs.config import config_options

simple_replace = [
    ("TAG-<num>", "http://gh/<num>", "TAG-123", "[TAG-123](http://gh/123)"),
    ("TAG-<num>", "http://gh/<num>", "x TAG-123", "x [TAG-123](http://gh/123)"),
    ("TAG-<num>", "http://gh/<num>", "TAG-123 x", "[TAG-123](http://gh/123) x"),
    ("TAG-<num>", "http://gh/<num>", "x TAG-123 y", "x [TAG-123](http://gh/123) y"),
    ("TAG-<num>", "http://gh/<num>", "x TAG-123 y", "x [TAG-123](http://gh/123) y"),
    ("TAG-<num>", "http://gh/TAG-<num>", "(TAG-123)", "([TAG-123](http://gh/TAG-123))"),
    (
        "TAG-<num>",
        "http://gh/TAG-<num>",
        "(TAG-12_3-4)",
        "([TAG-12_3-4](http://gh/TAG-12_3-4))",
    ),
    (
        "TAG-<num>",
        "http://gh/<num>",
        "x TAG-123 y TAG-456 z",
        "x [TAG-123](http://gh/123) y [TAG-456](http://gh/456) z",
    ),
    (
        "TAG-<num>",
        "http://gh/TAG-<num>",
        "TAG-Ab123dD",
        "[TAG-Ab123dD](http://gh/TAG-Ab123dD)",
    ),
]

complex_replace = [
    (
        "<some>-TAG-<num>-<ver>",
        "http://foo.bar/<some>?num=<num>&ver=<ver>",
        "file-TAG-123-XYZ",
        "[file-TAG-123-XYZ](http://foo.bar/file?num=123&ver=XYZ)",
    ),
]

ignore_already_linked = [
    (
        "TAG-<num>",
        "http://gh/<num>",
        "[TAG-789](http://gh/789)",
        "[TAG-789](http://gh/789)",
    ),
    (
        "TAG-<num>",
        "http://gh/TAG-<num>",
        "[TAG-789](http://gh/TAG-789)",
        "[TAG-789](http://gh/TAG-789)",
    ),
]

ignore_url_paths_when_filter_activated = [
    (
        "TAG-<num>",
        "http://gh/TAG-<num>",
        "[see TAG-789](http://gh/TAG-789)",
        "[see TAG-789](http://gh/TAG-789)",
    ),
    (
        "TAG-<num>",
        "http://gh/<num>",
        "[Go Here](http://gh/TAG-789) [Go There](http://gh/TAG-123)",
        "[Go Here](http://gh/TAG-789) [Go There](http://gh/TAG-123)",
    ),
]

ignore_url_paths_when_filter_deactivated = [
    (
        "TAG-<num>",
        "http://gh/TAG-<num>",
        "[see TAG-789](http://gh/TAG-789)",
        "[see [TAG-789](http://gh/TAG-789)](http://gh/TAG-789)",
    ),
    (
        "TAG-<num>",
        "http://gh/TAG-<num>",
        "[Go Here](http://gh/abcTAG-789) [Go There](http://gh/?blub=TAG-123)",
        "[Go Here](http://gh/abc[TAG-789](http://gh/TAG-789)) [Go There](http://gh/?blub=[TAG-123](http://gh/TAG-123))",
    ),
]

# This test cases address #4. Reference style links should be ignored.
ignore_ref_links = [
    ("TAG-<num>", "http://gh/<num>", "[TAG-456]", "[TAG-456]"),
    ("TAG-<num>", "http://gh/<num>", "[TAG-456][test456]", "[TAG-456][test456]"),
    ("TAG-<num>", "http://gh/<num>", "[TAG-456] [tag456]", "[TAG-456] [tag456]"),
    (
        "TAG-<num>",
        "http://gh/TAG-<num>",
        "[tag456]: http://gh/TAG-456",
        "[tag456]: http://gh/TAG-456",
    ),
]


def test_validation_of_missing_variable_in_target_url():
    values = [
        {
            "reference_prefix": "GH-",
            "target_url": "http://gh/TAG-",
        },
    ]
    with pytest.raises(config_options.ValidationError) as exc_info:
        AutoLinkOption().run_validation(values)
    assert exc_info.value.args[0] == "All variables must be used in 'target_url'"


def test_validation_of_at_least_one_variable_in_prefix_found_in_target_url():
    values = [
        {
            "reference_prefix": "GH-<num>",
            "target_url": "http://gh/TAG-<num>",
        },
    ]
    AutoLinkOption().run_validation(values)


@pytest.mark.parametrize(
    "ref_prefix, target_url, test_input, expected",
    simple_replace + complex_replace + ignore_already_linked + ignore_ref_links,
)
@pytest.mark.parametrize("filter_links", (True, False))
def test_parser(ref_prefix, target_url, test_input, expected, filter_links):
    result = autolink(test_input, ref_prefix, target_url, skip_links=True)
    assert result == expected


@pytest.mark.parametrize(
    "ref_prefix, target_url, test_input, expected",
    ignore_url_paths_when_filter_activated,
)
def test_activated_link_filter(ref_prefix, target_url, test_input, expected):
    result = autolink(test_input, ref_prefix, target_url, skip_links=True)
    assert result == expected


@pytest.mark.parametrize(
    "ref_prefix, target_url, test_input, expected",
    ignore_url_paths_when_filter_deactivated,
)
def test_deactivated_link_filter(ref_prefix, target_url, test_input, expected):
    result = autolink(test_input, ref_prefix, target_url, skip_links=False)
    assert result == expected


@pytest.mark.parametrize("skip_links", (True, False))
def test_with_attr_list(skip_links):
    markdown = "## Feature 1 { #F-001 .class-feature }"
    expected = "## Feature 1 { #F-001 .class-feature }"
    ref_prefix = "F-<num>"
    target_url = "http://gh/<num>"
    result = autolink(markdown, ref_prefix, target_url, skip_links=skip_links)
    assert result == expected


@pytest.mark.parametrize("skip_links", (True, False))
def test_multi_replace(skip_links):
    ref_prefix = "TAG-<num>"
    target_url = "http://gh/<num>"
    markdown = "TAG-1 TAG-1 TAG-1"
    expected = "[TAG-1](http://gh/1) [TAG-1](http://gh/1) [TAG-1](http://gh/1)"
    result = autolink(markdown, ref_prefix, target_url, skip_links=skip_links)
    assert result == expected

import pytest

from argref.main import AutoLinkWrapper
from argref.main import replace_autolink_references as autolink

simple_replace = [
    ("TAG-<num>", "http://gh/<num>", "TAG-123", "[TAG-123](http://gh/123)"),
    ("TAG-<num>", "http://gh/<num>", "x TAG-123", "x [TAG-123](http://gh/123)"),
    ("TAG-<num>", "http://gh/<num>", "TAG-123 x", "[TAG-123](http://gh/123) x"),
    ("TAG-<num>", "http://gh/<num>", "x TAG-123 y", "x [TAG-123](http://gh/123) y"),
    ("TAG-<num>", "http://gh/<num>", "x TAG-123 y", "x [TAG-123](http://gh/123) y"),
    ("TAG-<num>", "http://gh/TAG-<num>", "(TAG-123)", "([TAG-123](http://gh/TAG-123))"),
    ("TAG-", "http://forgot-num/<num>", "TAG-543", "[TAG-543](http://forgot-num/543)"),
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


def test_wrapper_with_enabled_link_filter():
    test_input = "[123](abc) [456](def) [789](ghi)"
    wrapper = AutoLinkWrapper(test_input, True)
    with wrapper as wrapped_markdown:
        assert wrapped_markdown.content == "___AUTOLINK_PLACEHOLDER_1___ ___AUTOLINK_PLACEHOLDER_2___ ___AUTOLINK_PLACEHOLDER_3___"

    assert wrapped_markdown.content == test_input


def test_wrapper_with_disabled_link_filter():
    test_input = "[123](abc) [456](def) [789](ghi)"
    wrapper = AutoLinkWrapper(test_input, False)
    with wrapper as wrapped_markdown:
        assert wrapped_markdown.content == test_input


@pytest.mark.parametrize(
    "ref_prefix, target_url, test_input, expected",
    simple_replace
    + complex_replace
    + ignore_already_linked
    + ignore_ref_links,
)
@pytest.mark.parametrize("filter_links", (True, False))
def test_parser(ref_prefix, target_url, test_input, expected, filter_links):
    wrapper = AutoLinkWrapper(test_input, filter_links)
    with wrapper as wrapped_mackdown:
        wrapped_mackdown.content = autolink(wrapped_mackdown.content, ref_prefix, target_url)
    assert wrapper.markdown == expected


@pytest.mark.parametrize(
    "ref_prefix, target_url, test_input, expected",
    ignore_url_paths_when_filter_activated,
)
def test_activated_link_filter(ref_prefix, target_url, test_input, expected):
    wrapper = AutoLinkWrapper(test_input, True)
    with wrapper as wrapped_mackdown:
        wrapped_mackdown.content = autolink(wrapped_mackdown.content, ref_prefix, target_url)
    assert wrapper.markdown == expected


@pytest.mark.parametrize(
    "ref_prefix, target_url, test_input, expected",
    ignore_url_paths_when_filter_deactivated,
)
def test_deactivated_link_filter(ref_prefix, target_url, test_input, expected):
    wrapper = AutoLinkWrapper(test_input, False)
    with wrapper as wrapped_mackdown:
        wrapped_mackdown.content = autolink(wrapped_mackdown.content, ref_prefix, target_url)
    assert wrapper.markdown == expected


# This test address #5. It currently only checks for '#' before the link
@pytest.mark.parametrize("filter_links", (True, False))
def test_with_attr_list(filter_links):
    text = "## Feature 1 { #F-001 .class-feature }"
    ref_prefix = "F-<num>"
    target_url = "http://gh/<num>"
    wrapper = AutoLinkWrapper(text, False)
    with wrapper as wrapped_mackdown:
        wrapped_mackdown.content = autolink(wrapped_mackdown.content, ref_prefix, target_url)
    assert wrapper.markdown == text


@pytest.mark.parametrize("filter_links", (True, False))
def test_multi_replace(filter_links):
    ref_prefix = "TAG-<num>"
    target_url = "http://gh/<num>"
    markdown = "TAG-1 TAG-1 TAG-1"
    expected = "[TAG-1](http://gh/1) [TAG-1](http://gh/1) [TAG-1](http://gh/1)"
    wrapper = AutoLinkWrapper(markdown, False)
    with wrapper as wrapped_mackdown:
        wrapped_mackdown.content = autolink(wrapped_mackdown.content, ref_prefix, target_url)
    assert wrapper.markdown == expected

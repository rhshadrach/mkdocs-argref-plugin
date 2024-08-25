import pytest

from mkdocs_argref_plugin.argref import replace_autolink_references as autolink


@pytest.mark.parametrize(
    "ref_prefix, target_url, test_input, expected",
    [
        ("TAG-<num>", "http://gh/<num>", "TAG-123", "[TAG-123](http://gh/123)"),
        ("TAG-<num>", "http://gh/<num>", "x TAG-123", "x [TAG-123](http://gh/123)"),
        ("TAG-<num>", "http://gh/<num>", "TAG-123 x", "[TAG-123](http://gh/123) x"),
        ("TAG-<num>", "http://gh/<num>", "x TAG-123 y", "x [TAG-123](http://gh/123) y"),
        ("TAG-<num>", "http://gh/<num>", "x TAG-123 y", "x [TAG-123](http://gh/123) y"),
        (
            "TAG-<num>",
            "http://gh/TAG-<num>",
            "(TAG-123)",
            "([TAG-123](http://gh/TAG-123))",
        ),
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
        (
            "<some>-TAG-<num>-<ver>",
            "http://foo.bar/<some>?num=<num>&ver=<ver>",
            "file-TAG-123-XYZ",
            "[file-TAG-123-XYZ](http://foo.bar/file?num=123&ver=XYZ)",
        ),
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
        ("TAG-<num>", "http://gh/<num>", "[TAG-456]", "[TAG-456]"),
        ("TAG-<num>", "http://gh/<num>", "[TAG-456][test456]", "[TAG-456][test456]"),
        ("TAG-<num>", "http://gh/<num>", "[TAG-456] [tag456]", "[TAG-456] [tag456]"),
        (
            "TAG-<num>",
            "http://gh/TAG-<num>",
            "[tag456]: http://gh/TAG-456",
            "[tag456]: http://gh/TAG-456",
        ),
    ],
)
@pytest.mark.parametrize("filter_links", (True, False))
def test_parser(ref_prefix, target_url, test_input, expected, filter_links):
    autolinks = [(ref_prefix, target_url)]
    result = autolink(test_input, autolinks, skip_links=True)
    assert result == expected


@pytest.mark.parametrize(
    "ref_prefix, target_url, test_input, expected",
    [
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
    ],
)
def test_activated_link_filter(ref_prefix, target_url, test_input, expected):
    autolinks = [(ref_prefix, target_url)]
    result = autolink(test_input, autolinks, skip_links=True)
    assert result == expected


@pytest.mark.parametrize(
    "ref_prefix, target_url, test_input, expected",
    [
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
            (
                "[Go Here](http://gh/abc[TAG-789](http://gh/TAG-789))"
                " [Go There](http://gh/?blub=[TAG-123](http://gh/TAG-123))"
            ),
        ),
    ],
)
def test_deactivated_link_filter(ref_prefix, target_url, test_input, expected):
    autolinks = [(ref_prefix, target_url)]
    result = autolink(test_input, autolinks, skip_links=False)
    assert result == expected


@pytest.mark.parametrize("skip_links", (True, False))
def test_with_attr_list(skip_links):
    markdown = "## Feature 1 { #F-001 .class-feature }"
    expected = "## Feature 1 { #F-001 .class-feature }"
    ref_prefix = "F-<num>"
    target_url = "http://gh/<num>"
    autolinks = [(ref_prefix, target_url)]
    result = autolink(markdown, autolinks, skip_links=skip_links)
    assert result == expected


@pytest.mark.parametrize("skip_links", (True, False))
def test_multi_replace(skip_links):
    ref_prefix = "TAG-<num>"
    target_url = "http://gh/<num>"
    markdown = "TAG-1 TAG-1 TAG-1"
    autolinks = [(ref_prefix, target_url)]
    expected = "[TAG-1](http://gh/1) [TAG-1](http://gh/1) [TAG-1](http://gh/1)"
    result = autolink(markdown, autolinks, skip_links=skip_links)
    assert result == expected


@pytest.mark.parametrize("skip_links", (True, False))
def test_multiple_patterns(skip_links):
    markdown = "TAG-1-X TAG-1 TAG-1-Y"
    autolinks = [
        ("TAG-<num>-<version>", "http://gh.com?doc=TAG-<num>&version=<version>"),
        ("TAG-<num>", "http://gh.com?doc=TAG-<num>"),
    ]
    if skip_links:
        expected = (
            "[TAG-1-X](http://gh.com?doc=TAG-1&version=X)"
            " [TAG-1](http://gh.com?doc=TAG-1)"
            " [TAG-1-Y](http://gh.com?doc=TAG-1&version=Y)"
        )
    else:
        expected = (
            "[TAG-1-X](http://gh.com?doc=[TAG-1](http://gh.com?doc=TAG-1)&version=X)"
            " [TAG-1](http://gh.com?doc=TAG-1)"
            " [TAG-1-Y](http://gh.com?doc=[TAG-1](http://gh.com?doc=TAG-1)&version=Y)"
        )
    result = autolink(markdown, autolinks, skip_links=skip_links)
    assert result == expected

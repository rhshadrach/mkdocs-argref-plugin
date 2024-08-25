from __future__ import annotations

import logging
import re
from typing import ClassVar

from mkdocs.config import config_options
from mkdocs.plugins import BasePlugin

log = logging.getLogger("mkdocs.plugins.mkdocs_argref_plugin")

# Regex capture group marker used for the full reference, e.g. `GH-123`
FULL_REF_TAG = "__ARGREF_ORIGINAL_TEXT__"
# Pattern to identify variables, e.g. `<num>`
VARIABLE_PATTERN = re.compile(r"(<\S+?>)")
# Pattern to identify links, e.g. `[link text](https://github.com/)`
LINK_PATTERN = re.compile(r"\[.+?\]\(.*?\)")
# Sentinel value template to avoid replacing links
LINK_PLACEHOLDER = "___AUTOLINK_PLACEHOLDER_{0}___"


class MarkdownAutoLinker:
    def __init__(self, reference, target_url):
        self.find_pattern = self._get_find_pattern(reference)
        self.replace_pattern = self._get_replace_pattern(target_url)

    @classmethod
    def _get_find_pattern(cls, reference):
        # Add named capture groups for each variable.
        reference_pattern = re.sub(VARIABLE_PATTERN, r"(?P\1[-\\w]+)", reference)

        # Combine with named capture group for the full reference.
        return re.compile(
            rf"(?<![#\[/])(?P<{FULL_REF_TAG}>" + reference_pattern + r")",
            re.IGNORECASE,
        )

    @classmethod
    def _get_replace_pattern(cls, target_url):
        template_for_linked_reference = rf"[<{FULL_REF_TAG}>]({target_url})"

        # Prefix variables with `\\g` to use named capture groups
        return re.sub(VARIABLE_PATTERN, r"\\g\1", template_for_linked_reference)

    def has_reference(self, markdown):
        return re.search(self.find_pattern, markdown) is not None

    def replace_all_references(self, markdown, skip_links: bool):
        if skip_links:
            pieces = re.split(LINK_PATTERN, markdown)
            urls = [*re.findall(LINK_PATTERN, markdown), ""]
            buf = []
            for piece, url in zip(pieces, urls):
                buf.append(re.sub(self.find_pattern, self.replace_pattern, piece) + url)
            result = "".join(buf)
        else:
            result = re.sub(self.find_pattern, self.replace_pattern, markdown)
        return result


def replace_autolink_references(
    markdown: str, autolinks: list[tuple[str, str]], skip_links: bool
):
    result = markdown
    for ref_prefix, target_url in autolinks:
        autolinker = MarkdownAutoLinker(ref_prefix, target_url)
        if autolinker.has_reference(result):
            result = autolinker.replace_all_references(result, skip_links)
    return result


class AutoLinkOption(config_options.OptionallyRequired):
    def run_validation(self, values):
        if not isinstance(values, list):
            raise config_options.ValidationError("Expected a list of autolinks.")
        for autolink in values:
            if "reference_prefix" not in autolink:
                raise config_options.ValidationError(
                    "Expected a 'reference_prefix' in autolinks."
                )
            if "target_url" not in autolink:
                raise config_options.ValidationError(
                    "Expected a 'target_url' in autolinks."
                )
            variables = re.findall(VARIABLE_PATTERN, autolink["reference_prefix"])
            if len(variables) == 0:
                variables = ["<num>"]
                autolink["reference_prefix"] += "<num>"
            if not all(v in autolink["target_url"] for v in variables):
                raise config_options.ValidationError(
                    "All variables must be used in 'target_url'"
                )
        return values


class AutolinkReference(BasePlugin):
    config_scheme = (
        ("autolinks", AutoLinkOption(required=True)),
        ("filter_links", config_options.Type(bool, default=False)),
    )
    autolinks: ClassVar[list[tuple[str, str]]] = []

    def on_pre_build(self, config, **kwargs) -> None:
        for autolink in self.config["autolinks"]:
            self.autolinks.append(
                (autolink["reference_prefix"], autolink["target_url"])
            )

    def on_page_markdown(self, markdown, **kwargs):
        """Takes an article written in markdown and looks for the
        presence of a ticket reference and replaces it with autual link
        to the ticket.

        :param markdown: Original article in markdown format
        :param kwargs: Other parameters (won't be used here)
        :return: Modified markdown
        """
        result = replace_autolink_references(
            markdown,
            self.autolinks,
            skip_links=self.config.get("filter_links", False),
        )
        return result

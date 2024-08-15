import logging
import re
from mkdocs.plugins import BasePlugin
from mkdocs.config import config_options


log = logging.getLogger("mkdocs.plugins.argref")

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
        self.reference_pattern = self._get_reference_pattern(reference)
        self.link_replace_text = self._get_link_replace_text(target_url)

    @classmethod
    def _get_reference_pattern(cls, reference):
        # Add named capture groups for each variable.
        reference_pattern = re.sub(VARIABLE_PATTERN, r"(?P\1[-\\w]+)", reference)

        # Combine with named capture group for the full reference.
        return re.compile(
            rf"(?<![#\[/])(?P<{FULL_REF_TAG}>" + reference_pattern + r")",
            re.IGNORECASE,
        )

    @classmethod
    def _get_link_replace_text(cls, target_url):
        template_for_linked_reference = rf"[<{FULL_REF_TAG}>]({target_url})"

        # Prefix variables with `\\g` to use named capture groups
        return re.sub(VARIABLE_PATTERN, r"\\g\1", template_for_linked_reference)

    def has_reference(self, markdown):
        return re.search(self.reference_pattern, markdown) is not None

    def replace_all_references(self, markdown):
        return re.sub(
            self.reference_pattern, self.link_replace_text, markdown
        )


class AutoLinkWrapper:
    class WrappedMarkdown:
        def __init__(self, content):
            """Container for markdown."""
            self.content = content

    def __init__(self, markdown, link_filter_enabled):
        """Possibly replace links with placeholders so they are not substituted.

        Args:
            markdown: Markdown content.
            link_filter_enabled: Whether to replace links with placeholders.
        """
        self.wrapped_markdown = AutoLinkWrapper.WrappedMarkdown(markdown)
        self.link_filter_enabled = link_filter_enabled
        self.links = []

    @property
    def markdown(self):
        return self.wrapped_markdown.content

    def filter_links(self):
        content = self.wrapped_markdown.content
        buf = ""
        while True:
            match = re.search(LINK_PATTERN, content)
            if match is None:
                buf += content
                break
            self.links.append(match.group(0))
            buf += content[: match.start()] + LINK_PLACEHOLDER.format(len(self.links))
            content = content[match.end(): ]
        self.wrapped_markdown.content = buf

    def recover_links(self):
        while len(self.links) > 0:
            self.wrapped_markdown.content = self.wrapped_markdown.content.replace(
                LINK_PLACEHOLDER.format(len(self.links)), self.links.pop()
            )

    def __enter__(self):
        if self.link_filter_enabled:
            self.filter_links()
        return self.wrapped_markdown

    def __exit__(self, exc_type, exc_value, traceback):
        if self.link_filter_enabled:
            self.recover_links()


def replace_autolink_references(markdown, ref_prefix, target_url):
    autolinker = MarkdownAutoLinker(ref_prefix, target_url)
    if autolinker.has_reference(markdown):
        markdown = autolinker.replace_all_references(markdown)
    return markdown


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
                raise config_options.ValidationError("All variables must be used in 'target_url'")
        return values


class AutolinkReference(BasePlugin):
    config_scheme = (
        ("autolinks", AutoLinkOption(required=True)),
        ("filter_links", config_options.Type(bool, default=False)),
    )

    def on_page_markdown(self, markdown, **kwargs):
        """
        Takes an article written in markdown and looks for the
        presence of a ticket reference and replaces it with autual link
        to the ticket.

        :param markdown: Original article in markdown format
        :param kwargs: Other parameters (won't be used here)
        :return: Modified markdown
        """
        link_filter_enabled = self.config.get("filter_links", False) is True
        wrapper = AutoLinkWrapper(markdown, link_filter_enabled)

        for autolink in self.config["autolinks"]:
            with wrapper as wrapped_markdown:
                wrapped_markdown.content = replace_autolink_references(
                    wrapped_markdown.content,
                    autolink["reference_prefix"],
                    autolink["target_url"],
                )

        return wrapper.markdown

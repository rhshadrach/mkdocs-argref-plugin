import re
from mkdocs.plugins import BasePlugin
from mkdocs.config import config_options


class MarkdownAutoLinker:
    original_tag = "__ARGREF_ORIGINAL_TEXT__"

    def __init__(self, markdown, reference, target_url):
        self.markdown = markdown
        self.reference_pattern = self._get_reference_pattern(reference)
        self.link_replace_text = self._get_link_replace_text(target_url)

    @classmethod
    def _get_reference_pattern(cls, reference):
        # ensure default <num> exists
        if "<num>" not in reference:
            reference = reference + "<num>"

        # make all variables like <...> in reference detectable
        reference_pattern = re.sub(
            re.compile(r"<(\S+?)>"), r"(?P<\1>[-\\w]+)", reference
        )

        # ensure original text is available
        return re.compile(
            rf"(?<![#\[/])(?P<{cls.original_tag}>" + reference_pattern + r")",
            re.IGNORECASE,
        )

    @classmethod
    def _get_link_replace_text(cls, target_url):
        # define template for markdown link
        template_for_linked_reference = rf"[<{cls.original_tag}>](" + target_url + r")"

        # make all variables like <...> in linked reference replacable
        return re.sub(r"\<(\S+?)\>", r"\\g<\1>", template_for_linked_reference)

    def markdown_has_reference(self):
        return re.search(self.reference_pattern, self.markdown) is not None

    def replace_all_references(self):
        self.markdown = re.sub(
            self.reference_pattern, self.link_replace_text, self.markdown
        )


class AutoLinkWrapper:
    link_pattern = re.compile(r"\[.+?\]\(.*?\)")
    placeholder = "___AUTOLINK_PLACEHOLDER_{0}___"

    class WrappedMarkdown:
        def __init__(self, content):
            self.__content = content

        @property
        def content(self):
            return self.__content
        
        @content.setter
        def content(self, content):
            self.__content = content

    def __init__(self, markdown, link_filter_enabled):
        self.wrapped_markdown = AutoLinkWrapper.WrappedMarkdown(markdown)
        self.link_filter_enabled = link_filter_enabled
        self.__links = []

    @property
    def markdown(self):
        return self.wrapped_markdown.content

    def filter_links(self):
        while True:
            match = re.search(self.link_pattern, self.wrapped_markdown.content)
            if match is None:
                break

            self.__links.append(match.group(0))
            self.wrapped_markdown.content = (
                self.wrapped_markdown.content[: match.start()]
                + self.placeholder.format(len(self.__links))
                + self.wrapped_markdown.content[match.end() :]
            )

    def recover_links(self):
        while len(self.__links) > 0:
            self.wrapped_markdown.content = self.wrapped_markdown.content.replace(
                self.placeholder.format(len(self.__links)), self.__links.pop()
            )

    def __enter__(self):
        if self.link_filter_enabled:
            self.filter_links()
        return self.wrapped_markdown

    def __exit__(self, exc_type, exc_value, traceback):
        if self.link_filter_enabled:
            self.recover_links()


def replace_autolink_references(markdown, ref_prefix, target_url):
    autolinker = MarkdownAutoLinker(markdown, ref_prefix, target_url)

    if not autolinker.markdown_has_reference():
        return autolinker.markdown

    autolinker.replace_all_references()

    return autolinker.markdown


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
            if "<num>" not in autolink["target_url"]:
                raise config_options.ValidationError("Missing '<num>' in 'target_url'.")

        return values


class AutolinkReference(BasePlugin):
    config_scheme = (("autolinks", AutoLinkOption(required=True)),)

    def on_page_markdown(self, markdown, **kwargs):
        """
        Takes an article written in markdown and looks for the
        presence of a ticket reference and replaces it with autual link
        to the ticket.

        :param markdown: Original article in markdown format
        :param kwargs: Other parameters (won't be used here)
        :return: Modified markdown
        """
        link_filter_enabled = autolink.get("filter_links", False) is True
        wrapper = AutoLinkWrapper(markdown, link_filter_enabled)

        with wrapper as wrapped_markdown:
            for autolink in self.config["autolinks"]:
                wrapped_markdown.content = replace_autolink_references(
                    wrapped_markdown.content,
                    autolink["reference_prefix"],
                    autolink["target_url"],
                )

        return wrapper.markdown

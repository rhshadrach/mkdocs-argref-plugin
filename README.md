# mkdocs-argref-plugin

[![PyPI - Version](https://img.shields.io/pypi/v/mkdocs-argref-plugin)](https://pypi.org/project/mkdocs-argref-plugin/)

This [mkdocs plugin](http://www.mkdocs.org/user-guide/plugins/)
allows users to convert text such as `GHI-123` in their documentation to a
corresponding URL, e.g. `https://github.com/myproject/issues/123`. Unlike similar
plugins, `argref` takes an argument for each reference that can be utilized
in the URL.


## Getting started
To install it, using `pip`:

```
pip install mkdocs-argref-plugin
```

Edit your `mkdocs.yml` file and add these few lines of code:

```yaml
plugins:
   - argref:
        filter_links: False  #default
        autolinks:
            - reference_prefix: GH-<num>
              target_url: https://github.com/myname/myproject/issues/<num>
            - reference_prefix: JIRA-<num>-<ver>
              target_url: https://jiracloud.com/myproject-<num>?ver=<ver>
```

- __filter_links__: When `True`, will not make replacements within existing markdown links. Caution: This may impact performance in large environments. Defaults to `False`.
- __reference_prefix__: This prefix appended by a number will generate a link any time it is found in a page. When no variable is present, will append `<num>` as the variable.
- __target_url__: The URL must contain all variables from `reference_prefix`.

### An example

For example, you could edit the `docs/index.md` file and insert the ticket references like this:

````markdown

Changelog:

- GHI-100: Add new feature.
- JIRA-231-XYZ: Fix bug.

````

This will be converted to:

```
Changelog:

- [GHI-100](https://github.com/myname/myproject/issues/100): Add new feature.
- [JIRA-231-XYZ](https://jiracloud.com/myproject-231?ver=XYZ): Fix bug.

```

## Changelog

### 0.5.0 (2024-08-25)

- Fix bug when `filter_links=True` and multiple autolinks are specified.

### 0.4.0 (2024-08-13)

- Added ability to use multiple references for each link and skip replacements within links.

### 0.3.0 (2024-06-07)

- Fixed bug where only one replacement would be made per page.

### 0.2.2 (2023-12-28)

- Allow extended set for <num> and ignore ref style links, already linked items, and attr_list cases with '#' before the ref

### 0.2.0
- Ignore already linked references.
- Converts text `[AF-100]` to a linked version and removes the brackets `AF-100`

## License

MIT

Originally built with ❤️ by [Saurabh Kumar](https://saurabh-kumar.com?ref=autolink-references-mkdocs-plugin)

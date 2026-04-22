# Documentation

## Build process

Using [Sphinx](https://www.sphinx-doc.org/en/master/) we automatically build the documentation using markdown files and docstrings from the code.

On pushes or pull requests to the main branch, the documentation is auto-built and available on [Readthedocs](https://readthedocs.org/).

## Including documentation

Since documentation is built from the code, every contribution should clearly state what component the documentation describes (for example a module, CLI tool, or feature page). After creating the content, make sure a reference to the source file lives in the appropriate subsection so that Sphinx can locate and render it.

### Markdown file

To document a new page that lives in a standalone markdown file, follow these steps:

1. Place the markdown file under the appropriate section in `docs/`. For example, how-to guides live in `docs/how-to/` and reference material belongs in `docs/reference/`. Any images should be placed in `docs/_images`.
2. In the pull request description (and any related communication), specify which page the new file documents so reviewers understand the context.
3. Update the corresponding section index (`autodocs/how-to.rst`, `autodocs/reference.rst`, etc.) to include your new page in its `.. toctree::`. Each index file keeps its toctree organized by the section's subsections, so add a line that points to the new markdown file (for example, `docs/how-to/new_guide.md`).

This ensures the page is discoverable from the rendered documentation and is built automatically by Sphinx.

### Module

To document a Python package or module, follow these steps:

1. In your change description, call out the module the documentation targets so the reviewer can verify coverage.
2. Add or update the module's `README.md` under `modules/<module_name>/README.md`. During the Sphinx build, `autodocs/conf.py` copies each module README into `autodocs/module_readmes/`, and `autodocs/modules.rst` automatically includes every file in that directory via a globbed toctree.
3. Make sure the module's docstrings are accurate. The `autodoc2_packages` setting in `autodocs/conf.py` lists the packages whose code documentation is generated automatically, so keeping docstrings up to date ensures the API reference stays correct.

Because the READMEs are gathered automatically, you only need to make sure the README exists alongside the module. The build will pick it up and render it in the Modules section.

By following these steps, you can ensure that your new markdown files and modules are properly integrated into the documentation, which will then be automatically built and made available on Readthedocs.

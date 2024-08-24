# See https://www.sphinx-doc.org/en/master/usage/configuration.html for all options

# Project information
project = "DataLogs"
copyright = "2023–2024, California Institute of Technology"
author = "Alex Hadley"
release = "0.5.0"

# Extensions
extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx_copybutton",
    "jupyter_sphinx",
]

# HTML output options
html_theme = "furo"
html_static_path = ["_static"]
html_context = {
  "display_github": True,
  "github_user": "PainterQubits",
  "github_repo": "datalogs",
  "github_version": "main/docs/",
}
# html_theme_options = {
#     "source_repository": "https://github.com/PainterQubits/datalogs",
#     "source_branch": "main",
#     "source_directory": "docs",
# }

# MyST options
myst_heading_anchors = 3

# Autodoc options
# See https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#configuration
autodoc_default_options = {
    "members": True,
    "inherited-members": True,
    "member-order": "bysource",
}
autodoc_type_aliases = {
    "datetime": "datetime.datetime",
    "ArrayLike": "numpy.typing.ArrayLike",
    "xr.Variable": "xarray.Variable",
    "xr.Dataset": "xarray.Dataset",
}
add_module_names = False

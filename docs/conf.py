# See https://www.sphinx-doc.org/en/master/usage/configuration.html for all options

# Project information
project = "DataLogger"
copyright = "2023, California Institute of Technology"
author = "Alex Hadley"
release = "0.1.0"

# General configuration
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

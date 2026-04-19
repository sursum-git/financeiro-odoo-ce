from . import core

# The Odoo ORM requires model modules to be imported from the
# `odoo.addons.*` namespace. This guard keeps pure Python unit tests
# runnable when the package is imported directly.
if __name__.startswith("odoo.addons."):
    from . import models
    from . import wizard

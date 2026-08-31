The ``graf`` package
====================

.. automodule:: graf
    :no-members:

Reading and writing
-------------------

.. autofunction:: graf.save_graf
.. autofunction:: graf.load_graf

The classes these return are documented in :doc:`base`.

Fonts
-----

These set what the generic font roles mean on this machine, and persist to a
per-user config file. They apply to every GrAF figure opened afterwards,
including files written elsewhere: the file states the author's intent, the
machine states your preference. See :doc:`fonts` for the model.

.. autofunction:: graf.set_font_default
.. autofunction:: graf.get_font_defaults
.. autofunction:: graf.add_font_path
.. autofunction:: graf.available_font_families
.. autofunction:: graf.user_config_path

Constants
---------

.. py:data:: graf.__version__

    Version of the installed ``graf-format`` library.

.. py:data:: graf.GRAF_FORMAT_VERSION

    Version of the on-disk *file format*, which moves independently of the
    library version. A reader uses this — not ``__version__`` — to decide
    whether it can read a file. See :doc:`../format`.

.. py:data:: graf.GENERIC_ROLES

    The generic font roles: ``serif``, ``sans-serif``, ``monospace``. Also
    available individually as ``graf.SERIF``, ``graf.SANS_SERIF`` and
    ``graf.MONOSPACE``.

Exceptions
----------

Importable as ``graf.GrafFormatError`` and ``graf.GrafVersionError``.

.. autoexception:: graf.base.GrafError
    :show-inheritance:

.. autoexception:: graf.base.GrafFormatError
    :show-inheritance:

.. autoexception:: graf.base.GrafVersionError
    :show-inheritance:

Re-exported classes
-------------------

For convenience these are importable from ``graf`` directly, and documented in
full in :doc:`base`:

:class:`~graf.base.Graf`,
:class:`~graf.base.GraphStyle`,
:class:`~graf.base.Font`,
:class:`~graf.base.Axis`,
:class:`~graf.base.Trace`,
:class:`~graf.base.Surface`,
:class:`~graf.base.Scale`,
:class:`~graf.base.MetaInfo`.

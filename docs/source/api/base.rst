``graf.base`` -- the file model
===============================

These classes mirror the structure of a ``.graf`` file one-to-one. The field
names below are the field names on disk, so this page doubles as a guide to the
:doc:`format specification <../format>`.

The figure
----------

.. autoclass:: graf.base.Graf
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: graf.base.MetaInfo
    :members:
    :undoc-members:
    :show-inheritance:

Axes and scales
---------------

.. autoclass:: graf.base.Axis
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: graf.base.Scale
    :members:
    :undoc-members:
    :show-inheritance:

Data
----

.. autoclass:: graf.base.Trace
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: graf.base.Surface
    :members:
    :undoc-members:
    :show-inheritance:

Styling
-------

.. autoclass:: graf.base.GraphStyle
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: graf.base.Font
    :members:
    :undoc-members:
    :show-inheritance:

Reading and writing
-------------------

.. autofunction:: graf.base.save_graf
.. autofunction:: graf.base.load_graf
.. autofunction:: graf.base.check_format_version
.. autofunction:: graf.base.is_legacy_version

Helpers
-------

.. autofunction:: graf.base.sample_colormap
.. autofunction:: graf.base.hexstr_to_rgb
.. autofunction:: graf.base.has_twinx

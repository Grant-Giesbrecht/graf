.. _api:

API reference
=============

GrAF's public API is re-exported from the top-level ``graf`` package, which is
the import most code should use::

    import graf

    graf.save_graf(fig, "figure.graf")
    fig = graf.load_graf("figure.graf")

The classes that make up a GrAF file are documented in :doc:`base`, and the font
model in :doc:`fonts`. For what any of it means on disk, see
:doc:`../format`.

.. toctree::
    :maxdepth: 2

    graf
    base
    fonts

.. image:: ../images/graf_banner.png
    :target: grafhome_
    :width: 700
    :align: center

|

**GrAF** (Graph Archive Format) is a file format for saving graphs — the data
and the formatting together — in a way that stays readable across languages and
across the years.

.. code-block:: python

    import graf
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    ax.plot(frequency, power, label='measured')
    ax.legend()

    graf.save_graf(fig, 'figure1.graf')     # data + formatting, both preserved
    fig = graf.load_graf('figure1.graf')    # reopen it anywhere, any time

GrAF does not promise a figure will look pixel-identical everywhere — fonts and
sizing vary between platforms. It promises that the parts carrying scientific
meaning survive: the data is stored as plain floats that are easy to read from
any language, and the formatting that makes a plot legible — axis limits and
scales, line types, markers, colours, labels, legends — comes back with it.

Installation
============

.. code-block:: bash

    pip install graf-format

Python 3.10+. Reading and writing ``.graf`` files needs nothing else.

The interactive viewer (``graf-viewer``, :func:`graf.widgets.rich_show`) is
built on Qt, which is a large download, so it is an optional extra:

.. code-block:: bash

    pip install 'graf-format[gui]'

Commands installed with the library:

.. code-block:: bash

    graf-upgrade -r ./figures                 # rewrite old files in the current format
    graf-viewer figure1.graf --serif --bold   # open and restyle  (needs [gui])

Documentation
=============

.. toctree::
    :maxdepth: 2
    :caption: Using GrAF

    tutorials/index

.. toctree::
    :maxdepth: 2
    :caption: Reference

    api/index
    format
    changelog
    license

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _grafhome: https://github.com/Grant-Giesbrecht/graf

``graf.fonts`` -- font specification
====================================

.. automodule:: graf.fonts
    :no-members:

Choosing fonts
--------------

.. autofunction:: graf.fonts.set_font_default
.. autofunction:: graf.fonts.get_font_defaults
.. autofunction:: graf.fonts.add_font_path
.. autofunction:: graf.fonts.available_font_families
.. autofunction:: graf.fonts.user_config_path

Stacks and roles
----------------

.. autofunction:: graf.fonts.normalize_stack
.. autofunction:: graf.fonts.ensure_role
.. autofunction:: graf.fonts.stack_role
.. autofunction:: graf.fonts.is_generic_role
.. autofunction:: graf.fonts.normalize_role
.. autofunction:: graf.fonts.normalize_weight
.. autofunction:: graf.fonts.normalize_style

Resolution
----------

.. autoclass:: graf.fonts.FontResolver
    :members:
    :undoc-members:

.. autofunction:: graf.fonts.resolve_font

Configuration
-------------

.. autofunction:: graf.fonts.load_manifest
.. autofunction:: graf.fonts.load_user_config
.. autofunction:: graf.fonts.save_user_config

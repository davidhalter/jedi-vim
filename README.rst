#################################################
jedi-vim - awesome Python autocompletion with VIM
#################################################

**now in beta testing phase**

*If you have any comments or feature requests, please tell me! I really want to
know, what you think about Jedi and jedi-vim.*

jedi-vim is a is a VIM binding to the awesome autocompletion library *Jedi*.

Here are some pictures:

.. image:: https://github.com/davidhalter/jedi/raw/master/docs/_screenshots/screenshot_complete.png

Completion for almost anything (Ctrl+Space).

.. image:: https://github.com/davidhalter/jedi/raw/master/docs/_screenshots/screenshot_function.png

Display of function/class bodies, docstrings.

.. image:: https://github.com/davidhalter/jedi/raw/master/docs/_screenshots/screenshot_pydoc.png

Pydoc support (with highlighting, Shift+k).

There is also support for goto and renaming.


Get the latest from `github <http://github.com/davidhalter/jedi-vim>`_.

You can get the Jedi library is documented
`here <http://github.com/davidhalter/jedi>`_.


Support
=======

The Jedi library supports most of Python's core features. From decorators to
generators, there is broad support.


Installation
============

You might want to use `pathogen <https://github.com/tpope/vim-pathogen>`_ to
install jedi in VIM. Also you need a VIM version that was compiled with
``+python``, which is typical for most distributions on Linux.

The first thing you need after that is an up-to-date version of Jedi. You can
either get it via ``pip install jedi`` or with ``git submodule update --init``
in your jedi-vim repository.

The autocompletion can be used with <ctrl+space>, if you want it to work with
<tab> you can use `supertab <https://github.com/ervandew/supertab>`_.

On Arch Linux, you can also install jedi-vim from AUR: `vim-jedi
<https://aur.archlinux.org/packages/vim-jedi/>`__.


Options
=======

Jedi is by default automatically initialized. If you don't want that I suggest
you disable the auto-initialization in your ``.vimrc``:

.. code-block:: vim

    let g:jedi#auto_initialization = 0

There are also some VIM options (like ``completeopt``) which are automatically
initialized, if you don't want that:

.. code-block:: vim

    let g:jedi#auto_vim_configuration = 0

The goto is by default on <leader g>. If you want to change that:

.. code-block:: vim

    let g:jedi#goto_command = "<leader>g"

``get_definition`` is by default on <leader d>. If you want to change that:

.. code-block:: vim

    let g:jedi#get_definition_command = "<leader>d"

Showing the pydoc is by default on ``K`` If you want to change that:

.. code-block:: vim

    let g:jedi#pydoc = "K"

If you are a person who likes to use VIM-buffers not tabs, you might want to
put that in your ``.vimrc``:

.. code-block:: vim

    let g:jedi#use_tabs_not_buffers = 0

Jedi automatically starts the completion, if you type a dot, e.g. ``str.``, if
you don't want this:

.. code-block:: vim

    let g:jedi#popup_on_dot = 0

Jedi selects the first line of the completion menu: for a better typing-flow and
usually saves one keypress.

.. code-block:: vim

    let g:jedi#popup_select_first = 0

There's some support for refactoring:

.. code-block:: vim

    let g:jedi#rename_command = "<leader>r"

And you can list all names that are related (have the same origin):

.. code-block:: vim

    let g:jedi#related_names_command = "<leader>n"

If you want to change the default autocompletion command:

.. code-block:: vim

    let g:jedi#autocompletion_command = "<C-Space>"

By default you get a window that displays the function definition you're
currently in. If you don't want that:

.. code-block:: vim

    let g:jedi#show_function_definition = "0"

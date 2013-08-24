#################################################
jedi-vim - awesome Python autocompletion with VIM
#################################################

.. image:: https://travis-ci.org/davidhalter/jedi-vim.png?branch=master
   :target: https://travis-ci.org/davidhalter/jedi-vim
   :alt: Travis-CI build status

jedi-vim is a is a VIM binding to the autocompletion library
`Jedi <http://github.com/davidhalter/jedi>`_.

Here are some pictures:

.. image:: https://github.com/davidhalter/jedi/raw/master/docs/_screenshots/screenshot_complete.png

Completion for almost anything (Ctrl+Space).

.. image:: https://github.com/davidhalter/jedi/raw/master/docs/_screenshots/screenshot_function.png

Display of function/class bodies, docstrings.

.. image:: https://github.com/davidhalter/jedi/raw/master/docs/_screenshots/screenshot_pydoc.png

Documentation (Pydoc) support (with highlighting, Shift+k).

There is also support for goto and renaming.


Get the latest from `github <http://github.com/davidhalter/jedi-vim>`_.

Documentation
=============

Documentation is available in your vim: ``:help jedi-vim``. You can also look
it up `on github <http://github.com/davidhalter/jedi-vim>`_.

You can read the Jedi library documentation `here <http://jedi.jedidjah.ch>`_.


Features
========

The Jedi library understands most of Python's core features. From decorators to
generators, there is broad support.

Apart from that, jedi-vim supports the following commands

- Completion ``<C-Space>``
- Goto assignments ``<leader>g`` (typical goto function)
- Goto definitions ``<leader>d`` (follow identifier as far as possible, includes
    imports and statements)
- Show Documentation/Pydoc ``K`` (shows a popup with assignments)
- Renaming ``<leader>r``
- Usages ``<leader>n`` (shows all the usages of a name)
- Open module, e.g. ``:Pyimport os`` (opens the ``os`` module)


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

There are also some VIM options (like ``completeopt`` and key defaults) which
are automatically initialized, but you can change all of them:

.. code-block:: vim

    let g:jedi#auto_vim_configuration = 0

``goto_assignments`` is by default on ``<leader g>``:

.. code-block:: vim

    let g:jedi#goto_assignments_command = "<leader>g"

``goto_definitions`` is by default on ``<leader d>``:

.. code-block:: vim

    let g:jedi#goto_definitions_command = "<leader>d"

Showing the pydoc documentation is by default on ``K``:

.. code-block:: vim

    let g:jedi#documentation_command = "K"

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

And you can list the usages of a name:

.. code-block:: vim

    let g:jedi#usages_command = "<leader>n"

If you want to change the default autocompletion command:

.. code-block:: vim

    let g:jedi#completions_command = "<C-Space>"

By default jedi-vim will display call signatures. If you don't want that:

.. code-block:: vim

    let g:jedi#show_call_signatures = "0"

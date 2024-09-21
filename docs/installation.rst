===========================
|EMODPY_hiv| installation
===========================

Follow the steps below to install |EMODPY_hiv|.

Prerequisites
=============

First, ensure the following prerequisites are met.

* Windows 10 Pro or Enterprise, Linux, or Mac

* |Python_supp| (https://www.python.org/downloads/release)

* A file that indicates the pip index-url:

    .. container:: os-code-block

        .. container:: choices

            * Windows
            * Linux

        .. container:: windows

            In C:\\Users\\Username\\pip\\pip.ini, containing the following::

                [global]
                index-url = https://packages.idmod.org/api/pypi/pypi-production/simple

        .. container:: linux

            In $HOME/.config/pip/pip.conf, containing the following::

                [global]
                index-url = https://packages.idmod.org/api/pypi/pypi-production/simple

Installation instructions
=========================

#.  Open a command prompt and create a virtual environment in any directory you choose. The
    command below names the environment "v-emodpy-hiv", but you may use any desired name::

        python -m venv v-emodpy-hiv

#.  Activate the virtual environment:

    .. container:: os-code-block

        .. container:: choices

            * Windows
            * Linux

        .. container:: windows

            Enter the following::

                v-emodpy-hiv\Scripts\activate

        .. container:: linux

            Enter the following::

                source v-emodpy-hiv/bin/activate

#.  Install |EMODPY_hiv| packages::

        pip install emodpy-hiv

    If you are on Python 3.6, also run::

        pip install dataclasses

    If you are on Linux, also run::

        pip install keyrings.alt

#.  When you are finished, deactivate the virtual environment by entering the following at a command prompt::

        deactivate

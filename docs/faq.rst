==========================
Frequently asked questions
==========================

As you get started with |EMODPY_hiv|, you may have questions. The most common
questions are answered below. For questions related to functionality in related 
packages, see :doc:`idmtools:faq` for |IT_s|, :doc:`emod_api:faq` for |emod_api|, 
and :doc:`emodpy:faq` for |EMODPY_s|.

How do I set configuration parameters?
	Define your own parameter-setting function such as ``set_param_fn`` and pass
	that function to the |EMODPY_s| task creator as the ``param_custom_cb``
	parameter. In that function, you can set the parameters directly. For
	example:

	.. literalinclude:: ../examples/start_here/example.py
	   :lines: 49-66

	See examples/start_here/example.py. for additional information.

	If you prefer something more modular, you can call a function in a standalone
	script/file that sets the configuration parameters.

Are there parameter defaults?
	Great question. If you don't set any configuration parameters, they will have
	defaults based on the schema. There are not yet configuration parameter
	defaults specific to HIV.

	The HIV team has some demographic parameter defaults set using
	:py:meth:`emodpy_hiv.demographics.DemographicsTemplates.AddDefaultSociety`.
	They can be seen below.

	.. literalinclude:: ../emodpy_hiv/demographics/DemographicsTemplates.py


I see lots of HIV_SIM examples. Are there any STI_SIM examples?
	Not at this time.

.. How do I specify the log level for |EMOD_s|? I get a schema error when I try to set it now.

.. There is an example of setting the |EMOD_s| parameter ``logLevel_default`` under 
.. examples/demo_scenario/conf.py using ``config_non_schema_params``. 

.. .. literalinclude:: ../examples/demo_scenario/conf.py
..    :lines: 64-76

I pip installed |EMODPY_hiv|, but I want to make changes. How should I do that?
	Install at a command prompt using the following::

		python package_setup.py develop

	This method is the most popular and proven, though there are some other
	options. Installing this way means that the |EMODPY_hiv| module in
	site-packages actually points to the same code as you have checked out in git.
	For more detail, see this `Stack Overflow post
	<https://stackoverflow.com/questions/19048732/python-setup-py-develop-vs-install#19048754>`_.

	However, we aim to get the desired changes quickly tested and included in the
	versioned module we release via pip install.

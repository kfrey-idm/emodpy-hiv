===
FAQ
===

As you get started with |EMODPY_hiv|, you may have questions. The most common
questions are answered below. For questions related to functionality in related 
packages, see :doc:`idmtools:faq` for |IT_s|, :doc:`emod_api:faq` for |emod_api|, 
and :doc:`emodpy:faq` for |EMODPY_s|.

.. contents:: Contents
   :local:

How do I set configuration parameters?
=========================================

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
================================

Great question. If you don't set any configuration parameters, they will have
defaults based on the schema. There are not yet configuration parameter
defaults specific to HIV.

The HIV team has some demographic parameter defaults set using
:py:meth:`emodpy_hiv.demographics.DemographicsTemplates.AddDefaultSociety`.
They can be seen in demographics/DemographicsTemplates.py.

How do I create a minimal campaign that just seeds an outbreak?
===============================================================

You can use the following code::

    def build_campaign():
        import emod_api.campaign as camp
        camp.set_schema( manifest.schema_path ) # don't worry about this for now
        import emodpy_hiv.interventions.outbreak as ob 

        event = ob.new_intervention( timestep=365, camp=camp, coverage=0.01 )
        camp.add( event )
        return camp

The code above creates a new intervention from the outbreak submodule that causes 1% of the population to
get an infection at timestep 365, and then adds that to the campaign. The only remaining thing to do is pass
the 'build_campaign' function to the task creator function ('from_default2' ). To see the documentation for
the hiv outbreak module go `here <https://docs.idmod.org/projects/emodpy-hiv/en/latest/emodpy_hiv.interventions.outbreak.html>`_.

How do I give a therapeutic intervention, like ART, to people?
=================================================================

We're going to divide this into 4 steps:

#. Import the `art module <https://docs.idmod.org/projects/emodpy-hiv/en/latest/emodpy_hiv.interventions.art.html#emodpy_hiv.interventions.art.new_intervention>`_ for creating the ART intervention.  
#. Create the ART intervention the way you want it.  
#. import and `emod_api.interventions.common module <https://docs.idmod.org/projects/emod-api/en/latest/emod_api.interventions.common.html#emod_api.interventions.common.ScheduledCampaignEvent>`_ for distribution interventions.  
#. Invoke the ScheduledCampaignEvent function.

Let's look at the code that will go into your build_campaign function:::

    def build_campaign():
        import emod_api.campaign as camp
        camp.set_schema( manifest.schema_path ) # don't worry about this for now
        import emodpy_hiv.interventions.art as art 
        import emod_api.interventions.common as com

        art_iv = art.new_intervention( camp )
        event1 = com.ScheduledCampaignEvent( camp, Start_Day=123, Intervention_List=[ art_iv ] )
        camp.add( event )

        event2 = com.ScheduledCampaignEvent( camp, Start_Day=366, Node_Ids=[ 1 ], Number_Repetitions = 10 Timesteps_Between_Repetitions = 14, Property_Restrictions = "Risk=High", 
                                             Demographic_Coverage = 0.04, Target_Age_Min=20*365, Target_Age_Max=25*365, Target_Gender = "Male", Intervention_List=[ art_iv ]) )
        camp.add( event )

The first 4 lines take care of our imports and initializating the campaign module with the schema. The next line creates the simplest possible intervention. Then we create a campaign event that distributes the ART intervention at timestep 123, and we add this to the campaign. Because we leave all the targeting parameters unspecified, the function uses the defaults, which basically means "everybody". In event2, we use all of the targeting and scheduling parameters to distributing ART every 2 weeks, 10 times in a row, starting at t=366, just in node 1, to 4% of the males between the ages of 20 and 25 in the "High Risk" group based on individual properties. Now in practice the repetitions don't make much sense because we're targeting the same people each rep as we got the first time, but it makes the point.

How do I give out an intervention to people based on a trigger instead of at a particular time?
==================================================================================================

The key part here is to use the `TriggeredCampaignEvent <https://docs.idmod.org/projects/emod-api/en/latest/emod_api.interventions.common.html#emod_api.interventions.common.TriggeredCampaignEvent>`_ function instead of ScheduledCampaignEvent. Let's look at the code:::

    def build_campaign():
        import emod_api.campaign as camp
        camp.set_schema( manifest.schema_path ) # don't worry about this for now
        import emodpy_hiv.interventions.art as art 
        import emod_api.interventions.common as com

        art_iv = art.new_intervention( camp )
        event1 = com.TriggeredCampaignEvent( camp, Start_Day=123, Event_Trigger="NewInfection", Intervention_List=[ art_iv ] )
        camp.add( event )

So we can see that the code is very similar, but we pass a new parameter to this new function, Event_Trigger. This can be any built-in event known to the model -- usually related to health events -- or an ad-hoc one you publish from another campaign event.

Are there are any helper functions to make this a little more concise?
=========================================================================

Yes. There is `a function <https://docs.idmod.org/projects/emodpy-hiv/en/latest/emodpy_hiv.interventions.cascade_helpers.html#emodpy_hiv.interventions.cascade_helpers.add_triggered_event>`_ to do most of the above for you. But you still create and pass the intervention itself.

What if I want to broadcast an event when I distribute the intervention?
===========================================================================

You can use the `BroadcastEvent <https://docs.idmod.org/projects/emod-api/en/latest/emod_api.interventions.common.html#emod_api.interventions.common.BroadcastEvent>`_ function and use that as the intervention or just one of multiple interventions.

What if I want to have a delay between the trigger (signal) and when the intervention is actually distributed?
=================================================================================================================

You may want to use `this function <https://docs.idmod.org/projects/emod-api/en/latest/emod_api.interventions.common.html#emod_api.interventions.common.triggered_campaign_delay_event>`_.

What if I want to change someone's Individual Property?
==========================================================

That's actually just an intervention, `PropertyValueChanger <https://docs.idmod.org/projects/emod-api/en/latest/emod_api.interventions.common.html#emod_api.interventions.common.PropertyValueChanger>`_. See an example of `this in action <https://github.com/InstituteforDiseaseModeling/emodpy-hiv/blob/master/examples/rakai/example.py#L82>`_.

Now I want to distribute tests and distribute interventions to only those who test positive?
============================================================================================

First, find the test `intervention <https://docs.idmod.org/projects/emodpy-hiv/en/latest/emodpy_hiv.interventions.rapiddiag.html>`_. This code should now seem unsurprising.::
 
    def build_campaign():
        import emod_api.campaign as camp
        camp.set_schema( manifest.schema_path )
        import emodpy_hiv.interventions.art as art 
        import emodpy_hiv.interventions.rapiddiag as diag 
        import emod_api.interventions.common as com

        diagnostic = diag.new_intervention( camp )
        art_iv = art.new_intervention( camp )
        test_event = com.TriggeredCampaignEvent( camp, Start_Day=1, Event_Trigger="NewInfection", Intervention_List=[ diagnostic ] )
        treat_event = com.TriggeredCampaignEvent( camp, Start_Day=1, Event_Trigger="TestedPositive", Intervention_List=[ art_iv ] )
        camp.add( test_event )
        camp.add( treat_event )

Testing everyone who is infected is obviously a bit naive but it just shows the idea.

I see lots of HIV_SIM examples. Are there any STI_SIM examples?
==================================================================

Not at this time.

.. How do I specify the log level for |EMOD_s|? I get a schema error when I try to set it now.

.. There is an example of setting the |EMOD_s| parameter ``logLevel_default`` under 
.. examples/demo_scenario/conf.py using ``config_non_schema_params``. 

.. .. literalinclude:: ../examples/demo_scenario/conf.py
..    :lines: 64-76

I pip installed |EMODPY_hiv|, but I want to make changes. How should I do that?
==================================================================================

Install at a command prompt using the following::

    python setup.py develop

This method is the most popular and proven, though there are some other
options. Installing this way means that the |EMODPY_hiv| module in
site-packages actually points to the same code as you have checked out in git.
For more detail, see this `Stack Overflow post
<https://stackoverflow.com/questions/19048732/python-setup-py-develop-vs-install#19048754>`_.

However, we aim to get the desired changes quickly tested and included in the
versioned module we release via pip install.

What's the command to get all the latest (stable) Python packages?
=====================================================================
::
    pip install emodpy_hiv --upgrade --upgrade-strategy eager


How do I install from conda?
=========================================

Once you have a conda environment created and activated, go ahead and conda install pip::

    conda install -n emodpy_env pip

And then pip install::

    pip install emodpy-hiv -i https://packages.idmod.org/api/pypi/pypi-production/simple


What is the difference between “Transitory” and “Informal” Relationships? 
=================================================================================
See :ref:`emod-hiv:relationships`. (Transitory relationships are like “one night stands" or commercial relationships whereas Informal are generally intended to represent pre-marital or extra-marital relationships of some length.)
 

How do Individual Properties like "Risk" change model behaviour if they are just tags?
===========================================================================================================================
The Demographics parameters docs (:doc:`emod-hiv:model-properties`) say that Individual Properties, such as risk and accessibility, do not add logic, in and of themselves. Then how does one make people at "high risk" actually have more sexual partners and other actually more risky behaviors?

The answer is two-fold: 1) Risk is actually a "special IP" in HIV_SIM that we use in PFA configuration. See the `set_concurrency_params_by_type_and_risk function <https://docs.idmod.org/projects/emodpy-hiv/en/latest/emodpy_hiv.demographics.HIVDemographics.html#emodpy_hiv.demographics.HIVDemographics.HIVDemographics.set_concurrency_params_by_type_and_risk>`_  for example; and 2) Behavioral interventions can be targeted to people based on Risk.


What is the difference between Individual-Targeted interventions and Node-Targeted interventions?
====================================================================================================
See :doc:`emod-generic:parameter-campaign-individual-interventions` and :doc:`emod-generic:parameter-campaign-node-interventions`. Node interventions tend to be much rarer and are usually "meta-interventions" that are really ways of distributing individual interventions.

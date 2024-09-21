from functools import partial
import inspect
from typing import List
import os

from emodpy.emod_task import EMODTask


class EMODHIVTask(EMODTask):
    """
    The EMODHIVTask class is a subclass of the EMODTask class from the emodpy.emod_task module. It is specifically
    designed to handle tasks related to the EMOD HIV model. It provides a function from_default() to create an
    EMODHIVTask object, which can then be used to run simulations, generate reports, and perform other tasks related
    to the EMOD HIV model.

    The subclass was created so that we could pass the schema path from the from_default() method into the
    build_campaign() method.  This was needed so that the path could be passed to a country model's
    build_campaign() method without requiring the user to create their own build function.  The country
    model's build_campaign() method needs the schema so that it can call set_schema() to reset the campaign's
    event array.

    This subclass also reduces the users need to know about the emodpy package.
    """
    @staticmethod
    def _has_argument(func, arg_name):
        """
        Check if a callable has a specific argument.

        Parameters:
        func (callable): The callable to check.
        arg_name (str): The name of the argument to look for.

        Returns:
        bool: True if the argument exists in the callable's signature, False otherwise.
        """
        signature = inspect.signature(func)
        return arg_name in signature.parameters

    @classmethod
    def _process_builder_func(cls, func, func_name, schema_path=None):
        """
        Validate and process a builder function.

        Args:
            func (callable): The function to validate and process.
            func_name (str): The name of the function.
            schema_path (str, optional): The schema path to use if the function is a campaign builder.

        Returns:
            callable: The processed function.
        """
        if func:
            if not callable(func):
                raise ValueError(f"The provided func parameter: {func_name} is not callable.")
            if func_name == "campaign_builder":
                if cls._has_argument(func, "schema_path"):
                    print(f"setting schema_path: {schema_path} to campaign_builder function.")
                    return partial(func, schema_path=schema_path)
                else:
                    return func
        return func

    @classmethod
    def from_default(
            cls,
            eradication_path: str,
            schema_path: str,
            param_custom_cb: callable = None,
            config_path: str = "config.json",
            campaign_builder: callable = None,
            demog_builder: callable = None,
            write_default_config: str = None,
            ep4_path=None,
            **kwargs) -> "EMODHIVTask":
        """
        Create an EMODHIVTask object for the EMOD HIV model.

        Args:
            eradication_path(str): The path to the eradication executable.
            schema_path(str): The path to the schema file.
            param_custom_cb(callable, optional): A custom callback function to update the config parameters. Default to None.
            config_path(str, optional): Optional filename for the generated config.json file. Default to "config.json".
            campaign_builder(callable, optional): A custom callback function to build the campaign. If this function takes a schema_path argument, it will be passed the schema_path. Default to None.
            demog_builder(callable, optional): A custom callback function to build the demographic configuration. Default to None.
            write_default_config(str, optional): If provided, it should be a file path where the default config will be written to. If it's set to None, no default config file will be written. default to None.
            ep4_path(str, optional): The path to the directory which contains the EP4(dtk_in_process.py, dtk_post_process.py and dtk_pre_process.py) scripts.
            **kwargs: Additional keyword arguments.

        Returns:
            EMODHIVTask: An EMODHIVTask object for the EMOD HIV model.

        """
        param_custom_cb = cls._process_builder_func(param_custom_cb, "param_custom_cb")
        campaign_builder = cls._process_builder_func(campaign_builder, "campaign_builder", schema_path)
        demog_builder = cls._process_builder_func(demog_builder, "demog_builder")

        if ep4_path is None:
            # set ep4_path and ep4_custom_cb to None
            return cls.from_default2(eradication_path=eradication_path, schema_path=schema_path,
                                     param_custom_cb=param_custom_cb, config_path=config_path,
                                     campaign_builder=campaign_builder, ep4_custom_cb=None,
                                     demog_builder=demog_builder, write_default_config=write_default_config,
                                     ep4_path=None, **kwargs)
        else:
            # check is ep4_path is a valid directory
            if not os.path.isdir(ep4_path):
                raise ValueError(f"The provided ep4_path: {ep4_path} is not a valid directory.")
            # keep ep4_custom_cb as default and pass ep4_path.
            return cls.from_default2(eradication_path=eradication_path, schema_path=schema_path,
                                     param_custom_cb=param_custom_cb, config_path=config_path,
                                     campaign_builder=campaign_builder,
                                     demog_builder=demog_builder, write_default_config=write_default_config,
                                     ep4_path=ep4_path, **kwargs)


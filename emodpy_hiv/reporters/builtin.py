from dataclasses import dataclass

from emodpy.reporters.base import BuiltInReporter
from emod_api import schema_to_class as s2c
from idmtools.assets import Asset
import json
import urllib.request


def add_report_hiv_by_age_and_gender(task, start_year: float = 1900, end_year: float = 2200,
                                     collect_gender_data: bool = False,
                                     collect_age_bins_data: list[float] = None,
                                     collect_circumcision_data: bool = False,
                                     collect_hiv_data: bool = False,
                                     collect_hiv_stage_data: bool = False,
                                     collect_on_art_data: bool = False,
                                     collect_ip_data: list[str] = None,
                                     collect_intervention_data: list[str] = None,
                                     add_transmitters: bool = False,
                                     stratify_infected_by_cd4: bool = False,
                                     event_counter_list: list[str] = None,
                                     add_relationships: bool = False,
                                     add_concordant_relationships: bool = False):
    """
    The age- and gender-stratified HIV report (ReportHIVByAgeAndGender.csv) provides a detailed set of HIV-related
    statistics, with numerous ways to customize and stratify the output. The report format facilitates further analysis
    using a pivot table.

    Some results, such as population size or number infected, are reported as single “snapshots” at the end of the
    reporting period. Other values, such as deaths or new infections, are aggregated for the entire reporting period.
    Further information on the output data types can be seen in the Output file data section:
    https://docs.idmod.org/projects/emod-hiv/en/latest/software-report-age-gender.html#output-file-data

    Args:
        task: task to which to add the reporter
        start_year: The simulation time in years to start collecting data. Default is 1900.
        end_year: The simulation time in years to stop collecting data. Default is 2200.
        collect_gender_data: When True, the report will be stratified by gender.
        collect_age_bins_data: A list of bins (age in years) used to stratify the report by age. Each value defines the
            minimum value (inclusive) of that bin, while the next value defines the maximum value (exclusive) of the
            bin. The values cannot be equal and must be listed in ascending order. Leave the array empty to not
            stratify the report by age. The maximum number of age bins is 100.
        collect_circumcision_data: When True, the IsCircumcised column is included in the output report. The report
            data will be stratified by those who do or do not have the MaleCircumcision intervention, with
            IsCircumcised = 1 for those with the intervention. Note: setting this to True doubles the number of rows
            in the output report.
        collect_hiv_data: When True, the HasHIV column is included in the output report. The report data will be
            stratified by those who do or do not have HIV. HasHIV = 1 for those with HIV. Cannot be used with
            Report_HIV_ByAgeAndGender_Collect_HIV_Stage_Data. Note: setting this to 1 doubles the number
            of rows in the output report.
        collect_hiv_stage_data: When True, the HIV_Stage column is included in the output report. The report
            data will be stratified by HIV Infection Stage (NOT_INFECTED, ACUTE, LATENT, AIDS, ON_ART). Cannot be
            used with collect_hiv_data (Report_HIV_ByAgeAndGender_Collect_HIV_Data) or collect_on_art_data
            (Report_HIV_ByAgeAndGender_Collect_On_Art_Data.)
            Note: setting this to True x5 the number of rows in the output report.
        collect_on_art_data: When set to 1, the On_ART column is included in the output report. The report data
            will be stratified by those individuals who are on ART (1) and those who are not (0). Cannot be used with
            Report_HIV_ByAgeAndGender_Collect_HIV_Stage_Data. Note: setting this to 1 doubles the number of rows in
            the output report.
        collect_ip_data: A list of individual property (IP) keys used to stratify the report. A column will be added to
            the report for each IP listed and a row for each possible IP Key:Value pair. Specify the IP keys and values
            by adding an IndividualProperties parameter in your demographics. For information on IndividualProperties,
            see https://docs.idmod.org/projects/emod-hiv/en/latest/model-properties.html
        collect_intervention_data: A list of interventions used to stratify the report. This allows for reporting on a
            subset (or all) of the interventions that an individual has been on, of those listed in the
            Intervention_Name campaign parameter. Note: this can only be used with interventions that remain with an
            individual for a period of time, such as VMMC, vaccine/PrEP, or those with a delay state in the cascade
            of care. For a list of possible interventions, see
            https://docs.idmod.org/projects/emod-hiv/en/latest/parameter-campaign-individual-interventions.html
        add_transmitters: When True, the Transmitters column is included in the output report. It indicates the total
            number of the individuals in that row who transmitted HIV during this reporting period. This may not add up
            to the number of new infections in the reporting period if any of the new infections were due to the
            OutbreakIndividual intervention or maternal transmission.
        stratify_infected_by_cd4: When True, the number of infected individuals will be segregated into four columns
            based on CD4 count ("Infected CD4 Under 200 (Not On ART)", "Infected CD4 200 to 349 (Not On ART)",
            "Infected CD4 350 to 499 (Not On ART)", "Infected CD4 500 Plus (Not On ART)") Note: this creates additional
            polling columns, but not more stratification rows.
        event_counter_list: A list of individual-level events to be used to stratify the report. A column will be added
            to the report for each event listed, showing the number of times the event occurred during the reporting for
            the people in the row. To be counted, the individual must qualify for the row stratification at the time
            the event occurred, not necessarily at the end of the reporting period (the individual themselves might end
            up being counted in a different row. See Built-In Event and Custom_Individual_Events lists for possible
            event values.
        add_relationships: When True, the report will contain data on the population currently in a relationship and
            ever in a relationship for each relationship type (TRANSITORY, INFORMAL, MARITAL, and COMMERCIAL),
            eight columns total. Additionally, columns containing a sum of individuals in two or more partnerships
            (Has Concurrent Partners) and a sum of the lifetime number of relationships (Lifetime Partners) will be
            included.
        add_concordant_relationships: When True, a Concordant column for each relationship type (TRANSITORY, INFORMAL,
            MARITAL, and COMMERCIAL) is included in the output report. These contain totals for each relationship of
            each type where both partners have the same HIV status.

    Returns:
        Nothing
    """
    # Documentation: https://docs.idmod.org/projects/emod-hiv/en/latest/software-report-age-gender.html
    if collect_hiv_stage_data and (collect_on_art_data or collect_hiv_data):
        raise ValueError("collect_hiv_stage_data cannot be used with collect_on_art_data or collect_hiv_data.")

    task.config.parameters.Report_HIV_ByAgeAndGender = 1
    task.config.parameters.Report_HIV_ByAgeAndGender_Start_Year = start_year
    task.config.parameters.Report_HIV_ByAgeAndGender_Stop_Year = end_year
    task.config.parameters.Report_HIV_ByAgeAndGender_Add_Concordant_Relationships = 1 if add_concordant_relationships else 0
    task.config.parameters.Report_HIV_ByAgeAndGender_Add_Relationships = 1 if add_relationships else 0
    task.config.parameters.Report_HIV_ByAgeAndGender_Add_Transmitters = 1 if add_transmitters else 0
    task.config.parameters.Report_HIV_ByAgeAndGender_Collect_Age_Bins_Data = collect_age_bins_data if collect_age_bins_data else []
    task.config.parameters.Report_HIV_ByAgeAndGender_Collect_Circumcision_Data = 1 if collect_circumcision_data else 0
    task.config.parameters.Report_HIV_ByAgeAndGender_Collect_Gender_Data = 1 if collect_gender_data else 0
    task.config.parameters.Report_HIV_ByAgeAndGender_Collect_HIV_Data = 1 if collect_hiv_data else 0
    task.config.parameters.Report_HIV_ByAgeAndGender_Collect_HIV_Stage_Data = 1 if collect_hiv_stage_data else 0
    task.config.parameters.Report_HIV_ByAgeAndGender_Collect_IP_Data = collect_ip_data if collect_ip_data else []
    task.config.parameters.Report_HIV_ByAgeAndGender_Collect_Intervention_Data = collect_intervention_data if collect_intervention_data else []
    task.config.parameters.Report_HIV_ByAgeAndGender_Collect_On_Art_Data = 1 if collect_on_art_data else 0
    task.config.parameters.Report_HIV_ByAgeAndGender_Event_Counter_List = event_counter_list if event_counter_list else []
    task.config.parameters.Report_HIV_ByAgeAndGender_Stratify_Infected_By_CD4 = 1 if stratify_infected_by_cd4 else 0


def add_report_relationship_start(task, start_year: float = 1900, end_year: float = 2200,
                                  node_ids: list = None,
                                  max_age_years: float = None,
                                  min_age_years: float = None,
                                  include_hiv_disease_statistics: bool = False,
                                  include_other_relationship_statistics: bool = False,
                                  individual_properties: list[str] = None,
                                  must_have_ip_key_value: str = "",
                                  must_have_intervention: str = ""):
    """
    The relationship formation report (RelationshipStart.csv) provides information about each relationship and its
    members, evaluated at the time of relationship formation. The report includes the relationship type, start time,
    scheduled end time, and detailed information about each participant: ID, gender, age, infection status,
    circumcision status for males, co-infections, number of relationships (active, recent, lifetime), and individual
    properties. The male in the relationship is indicated on the report as participant “A”, and the female as
    participant “B”.

    For more information, please see:
    https://docs.idmod.org/projects/emod-hiv/en/latest/software-report-relationship-start.html

    Args:
        task: task to which to add the reporter
        start_year: The simulation time in years to start collecting data. Default is 1900.
        end_year: The simulation time in years to stop collecting data. Default is 2200.
        node_ids: A list of nodes from which to collect data for the report. Leave the array empty None to collect data
            from all nodes.
        max_age_years: The age that of one of the partners must be less than or equal to for the relationship to
            be reported.
        min_age_years: The age that of one of the partners must be greater than or equal to for the relationship to
            be reported.
        include_hiv_disease_statistics: When True, the report will include information on CD4 count, viral load,
            disease stage, HIV positivity, and HIV testing results for each partner at the start of the relationship.
        include_other_relationship_statistics: When True, the report will include information on the number of active
            and lifetime relationships of each type (TRANSITORY, INFORMAL, MARITAL, and COMMERCIAL) for each partner in
            the relationship, as well as total relationships in the past six month and total lifetime relationships.
            Additionally, a bitmask column will indicate which types of concurrent relationships are allowed; these are
            configured using the Concurrency_Configuration parameter in the demographics, see:
            https://docs.idmod.org/projects/emod-hiv/en/latest/parameter-demographics.html#concurrency-configuration
        individual_properties: A list of strings individual property (IP) keys that will be included in the report as
            applicable to each partner at the start of the relationship. One column will be added to the report for
            each partner, for each key in the list. Specify the IP keys and values by adding an IndividualProperties
            parameter in your demographics. For information on IndividualProperties, see:
            https://docs.idmod.org/projects/emod-hiv/en/latest/model-properties.html
        must_have_ip_key_value: A string in format of "Key:Value", denoting specific IndividualProperty key and value,
            that one of the partners must have for the relationship to be reported. Empty string is to not
            filter by IndividualProperties, include everyone. For information on IndividualProperties, see:
            https://docs.idmod.org/projects/emod-hiv/en/latest/model-properties.html
        must_have_intervention: The name of an individual-level intervention (Intervention_Name parameter in campaign)
            that the one of the partners must have in order for the relationship to be reported. Empty string
            is to not filter by presence of individual, include everyone. For more information, see
            https://docs.idmod.org/projects/emod-hiv/en/latest/parameter-campaign-individual-interventions.html

    Returns:
        Nothing
    """

    task.config.parameters.Report_Relationship_Start = 1
    task.config.parameters.Report_Relationship_Start_Start_Year = start_year
    task.config.parameters.Report_Relationship_Start_End_Year = end_year
    task.config.parameters.Report_Relationship_Start_Node_IDs_Of_Interest = node_ids if node_ids else []
    if max_age_years:  # let Eradication use its own max
        task.config.parameters.Report_Relationship_Start_Max_Age_Years = max_age_years
    task.config.parameters.Report_Relationship_Start_Min_Age_Years = min_age_years if min_age_years else 0
    task.config.parameters.Report_Relationship_Start_Include_HIV_Disease_Statistics = 1 if include_hiv_disease_statistics else 0
    task.config.parameters.Report_Relationship_Start_Include_Other_Relationship_Statistics = 1 if include_other_relationship_statistics else 0
    task.config.parameters.Report_Relationship_Start_Individual_Properties = individual_properties if individual_properties else []
    task.config.parameters.Report_Relationship_Start_Must_Have_IP_Key_Value = must_have_ip_key_value
    task.config.parameters.Report_Relationship_Start_Must_Have_Intervention = must_have_intervention


# AKA ReportCoitalActs, should we use that?

def add_report_relationship_consummated(task, start_year: float = 1900, end_year: float = 2200,
                                        node_ids: list = None,
                                        max_age_years: float = None,
                                        min_age_years: float = None,
                                        relationship_type: str = None,
                                        has_intervention_with_name: bool = False,
                                        must_have_intervention: str = "",
                                        individual_properties: list[str] = None,
                                        partners_with_ip_key_value: list[str] = None,
                                        must_have_ip_key_value: str = ""):
    """
    The coital act report (RelationshipConsummated.csv) provides detailed information about each coital act that occurs
    during the simulation. The report includes unique identifiers for each coital act and relationship; the relationship
    type, number of acts, whether a condom was used, and whether transmission occurred; and detailed information about
    each participant, including age, gender, infection status, circumcision status, co-infection status, and treatment
    status. Each participant in a relationship is referred to as either participant “A” or participant “B”.

    One row of data is returned per coital act, and results are ordered on a per-relationship basis. Note: if a person
    is engaged in coital acts in multiple relationships during a time step, the order of those acts is unknown, only
    in which relationship they occurred. Additionally, if a person gets infected during a time step, they cannot
    re-transmit that infection during the same time step. The report does record during which coital act transmission
    occurred.

    If an uninfected person has coital acts with multiple infected partners during the same time step, all acts with the
    possibility of transmission are randomly ordered, so that the person has an equal chance of getting infected from
    any one of their partners. The probability of transmission from any one of these coital acts is still determined by
    the simulation parameters (number of acts, acquisition multipliers, etc.)

    For more information, please see:
    https://docs.idmod.org/projects/emod-hiv/en/latest/software-report-relationship-consummated.html

    Args:
        task: task to which to add the reporter
        start_year: The simulation time in years to start collecting data. Default is 1900.
        end_year: The simulation time in years to stop collecting data. Default is 2200.
        node_ids: A list of nodes from which to collect data for the report. Leave the array empty None to collect data
            from all nodes.
        max_age_years: The age that of one of the partners must be less than or equal to for the relationship to
            be reported.
        min_age_years: The age that of one of the partners must be greater than or equal to for the relationship to
            be reported.
        relationship_type: A string indicating the type of relationship the coital act has to occur in to be reported.
            Options are TRANSITORY, INFORMAL, MARITAL, and COMMERCIAL. Leave empty of None to include all relationship
            types.
        has_intervention_with_name: An array of intervention names where a column is added for each name.  1 if the
            person has the intervention, else 0.
        must_have_intervention: The name of an individual-level intervention (Intervention_Name parameter in campaign)
            that the one of the partners must have in order for the relationship to be reported. Empty string or None
            is to not filter by presence of individual, include everyone. For more information, see
            https://docs.idmod.org/projects/emod-hiv/en/latest/parameter-campaign-individual-interventions.html
        individual_properties: A list of strings individual property (IP) keys that will be included in the report as
            columns. Each person will have the value of that key in their row. You can specify the IP keys and values
            by adding an IndividualProperties parameter in your demographics. For information on IndividualProperties,
            see: https://docs.idmod.org/projects/emod-hiv/en/latest/model-properties.html
        partners_with_ip_key_value: A list of strings in format of "Key:Value", denoting specific IndividualProperty
            key:value pair. For each IP Key:Value string in the list, two columns will be added - one for each partner
            indicating the number of their partners for whom that IP Key:Value applies.
            For information on IndividualProperties, see:
            https://docs.idmod.org/projects/emod-hiv/en/latest/model-properties.html
        must_have_ip_key_value: A string in format of "Key:Value", denoting specific IndividualProperty key and value,
            that one of the partners must have for the relationship to be reported. Empty string or None is to not
            filter by IndividualProperties, include everyone. For information on IndividualProperties, see:
            https://docs.idmod.org/projects/emod-hiv/en/latest/model-properties.html

    Returns:
        Nothing
    """

    task.config.parameters.Report_Coital_Acts = 1
    task.config.parameters.Report_Coital_Acts_Start_Year = start_year
    task.config.parameters.Report_Coital_Acts_End_Year = end_year
    task.config.parameters.Report_Coital_Acts_Node_IDs_Of_Interest = node_ids if node_ids else []
    if max_age_years:  # let Eradication use its own max
        task.config.parameters.Report_Coital_Acts_Max_Age_Years = max_age_years
    task.config.parameters.Report_Coital_Acts_Min_Age_Years = min_age_years if min_age_years else 0
    task.config.parameters.Report_Coital_Acts_Relationship_Type = relationship_type if relationship_type else "NA"
    task.config.parameters.Report_Coital_Acts_Has_Intervention_With_Name = has_intervention_with_name if has_intervention_with_name else []
    task.config.parameters.Report_Coital_Acts_Individual_Properties = individual_properties if individual_properties else []
    task.config.parameters.Report_Coital_Acts_Must_Have_IP_Key_Value = must_have_ip_key_value
    task.config.parameters.Report_Coital_Acts_Must_Have_Intervention = must_have_intervention
    task.config.parameters.Report_Coital_Acts_Partners_With_IP_Key_Value = partners_with_ip_key_value if partners_with_ip_key_value else []


def add_report_relationship_end(task):
    """
    The relationship dissolution report (RelationshipEnd.csv) provides detailed information about each relationship and
    its members, evaluated at the time of relationship dissolution. The report includes the relationship type, start
    time, scheduled end time, actual end time (which may differ from the scheduled end time, for instance, due to the
    death of a partner), and information about each participant.

    For more information, please see:
    https://docs.idmod.org/projects/emod-hiv/en/latest/software-report-relationship-end.html

    Args:
        task: task to which to add the reporter

    Returns:
        Nothing
    """

    task.config.parameters.Report_Relationship_End = 1


def add_transmission_report(task):
    """
    The HIV relationship transmission report (TransmissionReport.csv) provides detailed information about each
    transmission event and relationship members, evaluated at the time of disease transmission within the relationship.
    It includes the time/date of transmission and information about the transmitter and recipient, including: age,
    gender, current and lifetime number of relationships, infection stage, circumcision status for males, co-infections,
    and disease-specific biomarkers, if applicable.

    For more information, please see:
    https://docs.idmod.org/projects/emod-hiv/en/latest/software-report-transmission.html

    Args:
        task: task to which to add the reporter

    Returns:
        Nothing
    """

    task.config.parameters.Report_Transmission = 1


def add_report_simulation_stats(task, manifest):
    """
    Adds ReportSimulationStats to collect data on the computational performance of the model
    (duration, memory, number of persisted interventions, etc.).

    There are no special parameter that need to be configured to generate the report.

    Args:
        task: task to which to add the reporter, if left as None, reporter is returned (used for unittests)
        manifest: schema path file

    Returns:
        if task is not set, returns the configured reporter, otherwise returns nothing
    """

    reporter = ReportSimulationStats()  # Create the reporter

    def rec_config_builder(params):  # not used yet
        return params

    reporter.config(rec_config_builder, manifest)
    if task:
        task.reporters.add_reporter(reporter)
    else:  # assume we're running a unittest
        return reporter


def add_report_event_counter(task, manifest,
                             start_day: int = 0,
                             end_day: int = None,
                             node_ids: list = None,
                             event_trigger_list: list = None,
                             min_age_years: float = 0,
                             max_age_years: float = None,
                             must_have_ip_key_value: str = "",
                             must_have_intervention: str = "",
                             filename_suffix: str = ""):
    """
    The event counter report (ReportEventCounter.json) is a JSON-formatted file that keeps track of how many of each
    individual-level event types occur during a time step. The report produced is similar to the InsetChart.json channel
    report, where there is one channel for each event defined in the configuration file (config.json). This report only
    counts events; a similar report, ReportEventRecorder, will provide information about the person at the time of the
    event.

    Args:
        task: task to which to add the reporter, if left as None, reporter is returned (used for unittests)
        manifest: schema path file
        start_day: the day of the simulation to start collecting data
        end_day: the day of simulation to stop collecting data
        node_ids: list of nodes in which to count the events
        event_trigger_list: list of individual-level events which to count
        min_age_years: Minimum age in years of people to collect data on
        max_age_years: Maximum age in years of people to collect data on
        must_have_ip_key_value: a "Key:Value" pair that the individual must have in order to be included. Empty string
            means don't look at IPs (individual properties)
        must_have_intervention: the name of the intervention that the person must have in order to be included.
            Empty string means don't look at the interventions
        filename_suffix: augments the filename of the report. If multiple reports are being generated,
            this allows you to distinguish among the multiple reports

    Returns:
        if task is not set, returns the configured reporter, otherwise returns nothing
    """

    reporter = ReportEventCounter()  # Create the reporter

    def rec_config_builder(params):
        params.Start_Day = start_day
        if end_day:  # let Eradication use its own max
            params.End_Day = end_day
        params.Event_Trigger_List = event_trigger_list if event_trigger_list else []
        if max_age_years:  # let Eradication use its own max
            params.Max_Age_Years = max_age_years
        params.Min_Age_Years = min_age_years
        params.Node_IDs_Of_Interest = node_ids if node_ids else []
        params.Must_Have_IP_Key_Value = must_have_ip_key_value
        params.Must_Have_Intervention = must_have_intervention
        params.Filename_Suffix = filename_suffix
        return params

    reporter.config(rec_config_builder, manifest)
    if task:
        task.reporters.add_reporter(reporter)
    else:  # assume we're running a unittest
        return reporter


def add_report_node_demographics(task, manifest,
                                 age_bins: list[float] = None,
                                 ip_key_to_collect: str = "",
                                 stratify_by_gender: bool = True):
    """
    The node demographics report (ReportNodeDemographics.csv) is a CSV-formatted report that provides population
    information stratified by node. For each time step, the report will collect data on each node and age bin.

    For more information:
    https://docs.idmod.org/projects/emod-hiv/en/latest/software-report-node-demographics.html

    Args:
        task: task to which to add the reporter, if left as None, reporter is returned (used for unittests)
        manifest: schema path file
        age_bins: the age bins (in years) to aggregate within and report. An empty array does not stratify by age. You
            must sort your input data from low to high.
        ip_key_to_collect: The name of the Individual Properties Key by which to stratify the report.
            An empty string or None does not stratify by Individual Properties
        stratify_by_gender: if True, to stratify by gender. False to not stratify by gender.

    Returns:
        if task is not set, returns the configured reporter, otherwise returns nothing
    """

    reporter = ReportNodeDemographics()  # Create the reporter

    def rec_config_builder(params):
        params.IP_Key_To_Collect = ip_key_to_collect
        params.Age_Bins = age_bins if age_bins else []
        params.Stratify_By_Gender = 1 if stratify_by_gender else 0
        return params

    reporter.config(rec_config_builder, manifest)
    if task:
        task.reporters.add_reporter(reporter)
    else:  # assume we're running a unittest
        return reporter


def add_event_recorder(task, event_list: list[str] = None,
                       only_include_events_in_list: bool = True,
                       ips_to_record: list[str] = None,
                       start_day: int = 0,
                       end_day: int = None,
                       node_ids: list = None,
                       min_age_years: float = 0,
                       max_age_years: float = None,
                       must_have_ip_key_value: str = "",
                       must_have_intervention: str = "",
                       property_change_ip_to_record: str = ""):
    """
    The health events and interventions report (ReportEventRecorder.csv) provides information on each individual’s
    demographics and health status at the time of an event. Additionally, it is possible to see the value of specific
    IndividualProperties, as assigned in the demographics file.

    For more information:
    https://docs.idmod.org/projects/emod-malaria/en/latest/software-report-event-recorder.html

    Args:
        task: task to which to add the reporter
        event_list: The list of individual-level events to include or exclude in the output report, based on how
            only_include_events_in_list is set.
        only_include_events_in_list: if True, only record events listed.  if False, record ALL events EXCEPT for the
            ones listed.
        ips_to_record: A list of strings individual property (IP) keys that will be included in the report as
            applicable to each partner at the start of the relationship. One column will be added to the report for
            each partner, for each key in the list. Specify the IP keys and values by adding an IndividualProperties
            parameter in your demographics. For information on IndividualProperties, see:
            https://docs.idmod.org/projects/emod-hiv/en/latest/model-properties.html
        start_day: The day of the simulation to start collecting data
        end_day: The day of the simulation to stop collecting data.
        node_ids: Data will be collected for the nodes in this list, if None or [] - all nodes have data collected.
        min_age_years: Minimum age in years of people to collect data on
        max_age_years: Maximum age in years of people to collect data on
        must_have_ip_key_value: A "Key:Value" pair string that the individual must have in order to be included.
            Empty string means don't look at IndividualProperties.
        must_have_intervention: The name of an individual-level intervention (Intervention_Name parameter in campaign)
            that the one of the partners must have in order for the relationship to be reported. Empty string or None
            is to not filter by presence of individual, include everyone. For more information, see
            https://docs.idmod.org/projects/emod-hiv/en/latest/parameter-campaign-individual-interventions.html
        property_change_ip_to_record: IndividualProperty key string for which recorder will add the PropertyChange event
            to the list of events that the report is listening to. However, it will only record the events where the
            property changed the value of this given key.
            For information on IndividualProperties, see:
            https://docs.idmod.org/projects/emod-hiv/en/latest/model-properties.html

    Returns:
        Nothing
    """

    if not event_list:
        if only_include_events_in_list:
            raise ValueError("You've indicated you want to only_include_events_in_list. Please define event_list "
                             "parameter.\n")
        else:
            event_list = []

    task.config.parameters.Report_Event_Recorder = 1
    task.config.parameters.Report_Event_Recorder_Events = event_list
    task.config.parameters.Report_Event_Recorder_Individual_Properties = ips_to_record if ips_to_record else []
    task.config.parameters.Report_Event_Recorder_Start_Day = start_day
    if end_day:  # let Eradication use its own max
        task.config.parameters.Report_Event_Recorder_End_Day = end_day
    task.config.parameters.Report_Event_Recorder_Node_IDs_Of_Interest = node_ids if node_ids else []
    if max_age_years:  # let Eradication use its own max
        task.config.parameters.Report_Coital_Acts_Max_Age_Years = max_age_years
    task.config.parameters.Report_Coital_Acts_Min_Age_Years = min_age_years if min_age_years else 0
    task.config.parameters.Report_Event_Recorder_Must_Have_IP_Key_Value = must_have_ip_key_value
    task.config.parameters.Report_Event_Recorder_Must_Have_Intervention = must_have_intervention
    task.config.parameters.Report_Event_Recorder_PropertyChange_IP_Key_Of_Interest = property_change_ip_to_record
    task.config.parameters.Report_Event_Recorder_Ignore_Events_In_List = 0 if only_include_events_in_list else 1


def add_report_hiv_art(task):
    """
    The ART initiation and discontinuation report (ReportHIVART.csv) provides information on individuals at time of
    ART initiation and discontinuation, including ID, age, gender, and CD4 count at ART initiation.

    For more information:
    https://docs.idmod.org/projects/emod-hiv/en/latest/software-report-hivart.html

    Args:
        task: task to which to add the reporter

    Returns:
        Nothing
    """

    task.config.parameters.Report_HIV_ART = 1


def add_report_hiv_infection(task,
                             start_year: float = 1900,
                             end_year: float = 2200):
    """
    The HIV disease progression report (ReportHIVInfection.csv) provides information on each individual’s disease state
    at each time step, including age, gender, CD4 count, survival prognosis, ART status, and factors impacting
    transmission and acquisition.

    For more information:
    https://docs.idmod.org/projects/emod-hiv/en/latest/software-report-hivinfection.html

    Args:
        task: task to which to add the reporter
        start_year: The simulation time in years to start collecting data. Default is 1900.
        end_year: The simulation time in years to stop collecting data. Default is 2200.

    Returns:
        Nothing
    """

    task.config.parameters.Report_HIV_Infection = 1
    task.config.parameters.Report_HIV_Infection_Start_Year = start_year
    task.config.parameters.Report_HIV_Infection_Stop_Year = end_year


def add_report_hiv_mortality(task):
    """
    The HIV mortality report (HIVMortality.csv) provides information about individuals at the time of their death,
    including disease status, CD4 count, medical history, and relationship history.

    For more information:
    https://docs.idmod.org/projects/emod-hiv/en/latest/software-report-hivmort.html

    Args:
        task: task to which to add the reporter

    Returns:
        Nothing
    """

    task.config.parameters.Report_HIV_Mortality = 1


def add_report_relationship_migration_tracking(task, manifest,
                                               start_year: float = 1900,
                                               end_year: float = 2200,
                                               node_ids: list[int] = None,
                                               min_age_years: float = 0,
                                               max_age_years: float = None,
                                               must_have_ip_key_value: str = "",
                                               must_have_intervention: str = "",
                                               filename_suffix: str = ""):
    """
    The relationship migration tracking report (ReportRelationshipMigrationTracking.csv) provides information about
    the relationships a person has when they are migrating. It will give information when they are leaving and entering
    a node. When leaving a node, the information will be about the status of the relationships just before they leave.
    When entering the new node, the information will be about the relationships that have been updated. For example,
    a person could leave with a relationship paused, find their partner in the new node, and get their relationship
    back to normal. This helps to know about how the status of the relationships have changed—migrated, paused, or
    terminated.

    The person initiating a migration event will first have their relationships listed in the state before migrating
    starts. If a partner is asked to migrate with them, then that partner’s relationships will also be listed. When the
    people are immigrating into the new node, the list of relationships that are continuing in the new node will be
    listed. Any migrated partner should only have the relationship with the partner initiating migration. Their other
    relationships will have been terminated.

    For more information:
    https://docs.idmod.org/projects/emod-hiv/en/latest/software-report-relationship-migration-tracking.html

    Args:
        task: task to which to add the reporter, if left as None, reporter is returned (used for unittests)
        manifest: schema path file
        start_year: The simulation time in years to start collecting data. Default is 1900.
        end_year: The simulation time in years to stop collecting data. Default is 2200.
        node_ids: A list of nodes from which to collect data for the report. Leave the array empty None to collect data
            from all nodes.
        max_age_years: The age that of one of the partners must be less than or equal to for the relationship to
            be reported.
        min_age_years: The age that of one of the partners must be greater than or equal to for the relationship to
            be reported.
        must_have_intervention: The name of an individual-level intervention (Intervention_Name parameter in campaign)
            that the one of the partners must have in order for the relationship to be reported. Empty string or None
            is to not filter by presence of individual, include everyone. For more information, see
            https://docs.idmod.org/projects/emod-hiv/en/latest/parameter-campaign-individual-interventions.html
        must_have_ip_key_value: A string in format of "Key:Value", denoting specific IndividualProperty key and value,
            that one of the partners must have for the relationship to be reported. Empty string or None is to not
            filter by IndividualProperties, include everyone. For information on IndividualProperties, see:
            https://docs.idmod.org/projects/emod-hiv/en/latest/model-properties.html
        filename_suffix: Augments the filename of the report. This allows you to generate multiple reports by
            distinguishing among them.


    Returns:
        if task is not set, returns the configured reporter, otherwise returns nothing
    """

    reporter = ReportRelationshipMigrationTracking()  # Create the reporter

    def rec_config_builder(params):
        params.Start_Year = start_year
        if end_year:  # let Eradication use its own max
            params.End_Year = end_year
        if max_age_years:  # let Eradication use its own max
            params.Max_Age_Years = max_age_years
        params.Min_Age_Years = min_age_years
        params.Node_IDs_Of_Interest = node_ids if node_ids else []
        params.Must_Have_IP_Key_Value = must_have_ip_key_value
        params.Must_Have_Intervention = must_have_intervention
        params.Filename_Suffix = filename_suffix
        return params

    reporter.config(rec_config_builder, manifest)
    if task:
        task.reporters.add_reporter(reporter)
    else:  # assume we're running a unittest
        return reporter


def add_human_migration_tracking(task, manifest):
    """
    The human migration tracking report (ReportHumanMigrationTracking.csv) is a CSV-formatted report that provides
    details about human travel during simulations. The finished report will provide one line for each surviving
    individual that migrates during the simulation. The simulation must have migration enabled.

    For more information:
    https://docs.idmod.org/projects/emod-hiv/en/latest/software-report-human-migration.html

    Args:
        task: task to which to add the reporter, if left as None, reporter is returned (used for unittests)
        manifest: schema path file

    Returns:
        if task is not set, returns the configured reporter, otherwise returns nothing
    """

    reporter = ReportHumanMigrationTracking()  # Create the reporter

    def rec_config_builder(params):  # not used yet
        return params

    reporter.config(rec_config_builder, manifest)
    if task:
        task.reporters.add_reporter(reporter)
    else:  # assume we're running a unittest
        return reporter


@dataclass
class ReportHumanMigrationTracking(BuiltInReporter):
    """
        The human migration tracking report is a CSV-formatted report (ReportHumanMigrationTracking.csv) that provides
        details about human travel during simulations. The report provides one line for each surviving individual who
        migrates during the simulation.
    """

    def config(self, config_builder, manifest):
        self.class_name = "ReportHumanMigrationTracking"
        report_params = s2c.get_class_with_defaults("ReportHumanMigrationTracking", manifest.schema_file)
        report_params = config_builder(report_params)
        report_params.finalize()
        report_params.pop("Sim_Types")
        self.parameters.update(dict(report_params))


@dataclass
class ReportRelationshipMigrationTracking(BuiltInReporter):
    """
    See add_report_relationship_migration_tracking for more information.
    """

    def config(self, config_builder, manifest):
        self.class_name = "ReportRelationshipMigrationTracking"
        report_params = s2c.get_class_with_defaults("ReportRelationshipMigrationTracking", manifest.schema_file)
        report_params = config_builder(report_params)
        report_params.finalize()
        report_params.pop("Sim_Types")
        self.parameters.update(dict(report_params))


@dataclass
class ReportEventCounter(BuiltInReporter):
    """
        The event counter report is a JSON-formatted file (ReportEventCounter.json) that keeps track of how many of
        each event types occurs during a time step. The report produced is similar to the InsetChart.json channel
        report, where there is one channel for each event defined in the configuration file (config.json).
    """

    def config(self, config_builder, manifest):
        self.class_name = "ReportEventCounter"
        report_params = s2c.get_class_with_defaults("ReportEventCounter", manifest.schema_file)
        report_params = config_builder(report_params)
        report_params.finalize()
        report_params.pop("Sim_Types")
        self.parameters.update(dict(report_params))


@dataclass
class ReportSimulationStats(BuiltInReporter):
    """
    Adds ReportSimulationStats to collect data on the computational performance of the model
    (duration, memory, number of persisted interventions, etc).
    """

    def config(self, config_builder, manifest):
        self.class_name = "ReportSimulationStats"
        report_params = s2c.get_class_with_defaults("ReportSimulationStats", manifest.schema_file)
        report_params = config_builder(report_params)
        report_params.finalize()
        report_params.pop("Sim_Types")
        self.parameters.update(dict(report_params))


@dataclass
class ReportNodeDemographics(BuiltInReporter):
    """
        The node demographics report is a CSV-formatted report (ReportNodeDemographics.csv) that provides population
        information stratified by node. For each time step, the report collects data on each node and age bin.
    """

    def config(self, config_builder, manifest):
        self.class_name = "ReportNodeDemographics"
        report_params = s2c.get_class_with_defaults("ReportNodeDemographics", manifest.schema_file)
        report_params = config_builder(report_params)
        report_params.finalize()
        report_params.pop("Sim_Types")
        self.parameters.update(dict(report_params))

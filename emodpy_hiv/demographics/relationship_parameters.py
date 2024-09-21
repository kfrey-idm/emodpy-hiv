from typing import Dict

from emod_api.demographics.Updateable import Updateable
from emod_api.utils import Distributions

from emodpy_hiv.demographics.condom_usage_parameters import CondomUsageParameters


class RelationshipParameters(Updateable):
    def __init__(self,
                 condom_usage: CondomUsageParameters = None,
                 coital_act_rate: float = 0,
                 duration: Dict = None):
        """
        A RelationshipParameters object defines basic attributes such as relationship duration, what happens if one
        member of a relationship migrates, and condom usage.

        https://docs.idmod.org/projects/emod-hiv/en/latest/parameter-demographics.html#relationship-parameters

        Args:
            condom_usage: a CondomUsageParameters object defining condom usage over time
            coital_act_rate: the probability of a coital act occurring at each time step
            duration: a (weibull) duration dict used for determining relationship duration
        """
        super().__init__()
        self.condom_usage = condom_usage if condom_usage is not None else CondomUsageParameters()
        self.coital_act_rate = coital_act_rate
        # TODO: do we need to allow alteration of migration actions??
        self.migration_actions = ["TERMINATE"]
        self.migration_actions_distribution = [1.0]

        # TODO: consider, is it ok for this to NOT be an Updateable? Or should the two contained params just be part of RelationshipParameters?
        default_duration = Distributions.weibull(weibull_lambda=0, weibull_kappa=0)
        self.duration = duration if duration is not None else default_duration
        if self.duration['Distribution'] != 'WEIBULL_DISTRIBUTION':
            raise ValueError(f"Only weibull distributed relationship durations accepted. "
                             f"Received: {self.duration['Distribution']}")

    def to_dict(self) -> Dict:
        parameters = {
            'Condom_Usage_Probability': self.condom_usage.to_dict(),
            'Coital_Act_Rate': self.coital_act_rate,
            'Duration_Weibull_Scale': self.duration['Lambda'],
            'Duration_Weibull_Heterogeneity': self.duration['Kappa'] ** -1,
            'Migration_Actions': self.migration_actions,
            'Migration_Actions_Distribution': self.migration_actions_distribution
        }
        return parameters

    @classmethod
    def from_dict(cls, d: Dict) -> '__class__':
        condom_usage = CondomUsageParameters.from_dict(d=d['Condom_Usage_Probability'])
        duration = Distributions.weibull(weibull_lambda=d['Duration_Weibull_Scale'],
                                         weibull_kappa=d['Duration_Weibull_Heterogeneity'])
        return cls(condom_usage=condom_usage, coital_act_rate=d['Coital_Act_Rate'], duration=duration)

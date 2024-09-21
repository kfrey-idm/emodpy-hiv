from enum import Enum


class RelationshipTypes(Enum):
    """
    Aid to reduce direct string comparisons of standard HIV-model relationship types and associated errors.
    e.g. Use RelationshipTypes.transitory or RelationshipTypes.transitory.name in code depending on use and
    RelationshipTypes.transitory.value in json/dict values.
    """
    transitory = 'TRANSITORY'
    informal = 'INFORMAL'
    marital = 'MARITAL'
    commercial = 'COMMERCIAL'

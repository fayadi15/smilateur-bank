from . import inspect_credit_amenagement
from . import inspect_credit_conso
from . import inspect_credit_habitat
from . import inspect_credit_voiture

BH_INSPECTS = {
    inspect_credit_amenagement.KEY: inspect_credit_amenagement,
    inspect_credit_conso.KEY: inspect_credit_conso,
    inspect_credit_habitat.KEY: inspect_credit_habitat,
    inspect_credit_voiture.KEY: inspect_credit_voiture,
}

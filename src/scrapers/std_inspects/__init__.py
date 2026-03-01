from . import inspect_credit_immobilier
from . import inspect_credit_auto
from . import inspect_credit_conso

STD_INSPECTS = {
    "CREDIT_IMMOBILIER": inspect_credit_immobilier,
    "CREDIT_AUTO": inspect_credit_auto,
    "CREDIT_CONSO": inspect_credit_conso,
}
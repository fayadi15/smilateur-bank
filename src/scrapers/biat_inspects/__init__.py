from . import inspect_credimedia
from . import inspect_crediauto
from . import inspect_credirenov
from . import inspect_credifoyer
from . import inspect_biatimmo
from . import inspect_fleximmo
from . import inspect_awal_sakan
from . import inspect_crediresidence

BIAT_INSPECTS = {
    "CREDIMEDIA": inspect_credimedia,
    "CREDIAUTO": inspect_crediauto,
    "CREDIRENOV": inspect_credirenov,
    "CREDIFOYER": inspect_credifoyer,
    "BIATIMMO": inspect_biatimmo,
    "FLEXIMMO": inspect_fleximmo,
    "AWAL_SAKAN": inspect_awal_sakan,
    "CREDIRESIDENCE": inspect_crediresidence,
}
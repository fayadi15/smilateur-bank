from .inspect_pre_salaire_amenagement import InspectPreSalaireAmenagement
from .inspect_auto_invest import InspectAutoInvest
from .inspect_credim_watani import InspectCredimWatani

AMEN_INSPECTS = {
    InspectPreSalaireAmenagement.KEY: InspectPreSalaireAmenagement,
    InspectAutoInvest.KEY: InspectAutoInvest,
    InspectCredimWatani.KEY: InspectCredimWatani,
}

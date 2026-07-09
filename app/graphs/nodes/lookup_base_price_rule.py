from app.core.constants import ValidityLabel
from app.graphs.state import EstimateState
from app.services.price_reference_service import PriceReferenceService


def lookup_base_price_rule(state: EstimateState) -> EstimateState:
    if state.get("validity_label") != ValidityLabel.VALID_REPAIR_REQUEST.value:
        return state
    rule = PriceReferenceService().find_price_rule(
        main_category=state.get("main_category"),
        object_label=state.get("object_label"),
        problem_label=state.get("problem_label"),
        repair_task=state.get("repair_task"),
    )
    state["base_price_rule"] = rule
    state["base_price_found"] = rule is not None
    return state


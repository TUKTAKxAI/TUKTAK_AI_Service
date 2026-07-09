from langgraph.graph import END, START, StateGraph

from app.graphs.nodes.analyze_text import analyze_text
from app.graphs.nodes.calculate_estimate import (
    calculate_estimate_from_similar_cases,
    calculate_estimate_with_base_price_and_llm,
    validate_estimate_result,
)
from app.graphs.nodes.check_image_quality import check_image_quality
from app.graphs.nodes.lookup_base_price_rule import lookup_base_price_rule
from app.graphs.nodes.route_image_similarity_needed import mark_image_similarity_route
from app.graphs.nodes.search_similar_cases import (
    evaluate_similar_cases,
    text_and_image_similarity_search,
    text_similarity_search,
)
from app.graphs.nodes.validate_input import validate_input
from app.graphs.nodes.validate_text import validate_text
from app.graphs.routes import route_image_similarity_needed, route_similar_cases_enough
from app.graphs.state import EstimateState


def build_estimate_graph():
    graph = StateGraph(EstimateState)
    graph.add_node("validate_input", validate_input)
    graph.add_node("check_image_quality", check_image_quality)
    graph.add_node("validate_text", validate_text)
    graph.add_node("analyze_text", analyze_text)
    graph.add_node("lookup_base_price_rule", lookup_base_price_rule)
    graph.add_node("mark_image_similarity_route", mark_image_similarity_route)
    graph.add_node("text_similarity_search", text_similarity_search)
    graph.add_node("text_and_image_similarity_search", text_and_image_similarity_search)
    graph.add_node("evaluate_similar_cases", evaluate_similar_cases)
    graph.add_node("calculate_estimate_from_similar_cases", calculate_estimate_from_similar_cases)
    graph.add_node("calculate_estimate_with_base_price_and_llm", calculate_estimate_with_base_price_and_llm)
    graph.add_node("validate_estimate_result", validate_estimate_result)

    graph.add_edge(START, "validate_input")
    graph.add_edge("validate_input", "check_image_quality")
    graph.add_edge("check_image_quality", "validate_text")
    graph.add_edge("validate_text", "analyze_text")
    graph.add_edge("analyze_text", "lookup_base_price_rule")
    graph.add_edge("lookup_base_price_rule", "mark_image_similarity_route")
    graph.add_conditional_edges(
        "mark_image_similarity_route",
        route_image_similarity_needed,
        {
            "text_similarity_search": "text_similarity_search",
            "text_and_image_similarity_search": "text_and_image_similarity_search",
        },
    )
    graph.add_edge("text_similarity_search", "evaluate_similar_cases")
    graph.add_edge("text_and_image_similarity_search", "evaluate_similar_cases")
    graph.add_conditional_edges(
        "evaluate_similar_cases",
        route_similar_cases_enough,
        {
            "calculate_estimate_from_similar_cases": "calculate_estimate_from_similar_cases",
            "calculate_estimate_with_base_price_and_llm": "calculate_estimate_with_base_price_and_llm",
        },
    )
    graph.add_edge("calculate_estimate_from_similar_cases", "validate_estimate_result")
    graph.add_edge("calculate_estimate_with_base_price_and_llm", "validate_estimate_result")
    graph.add_edge("validate_estimate_result", END)
    return graph.compile()


estimate_graph = build_estimate_graph()


from services.search_service import hyper_search_aiml

VALID_DEPTHS = {"basic", "advanced"}
VALID_FORMATS = {"full", "summary", "links_only"}

def search_aiml(
    query: str,
    depth: str = "advanced",
    format: str = "full",
    max_results: int = 10
) -> dict | list:
    if depth not in VALID_DEPTHS:
        raise ValueError(f"depth must be one of {VALID_DEPTHS}")
    if format not in VALID_FORMATS:
        raise ValueError(f"format must be one of {VALID_FORMATS}")

    max_results = max(1, min(20, max_results))
    results = hyper_search_aiml(query, depth, max_results)

    if format == "links_only":
        return [{"title": r["title"], "url": r["url"]} for r in results["results"]]

    if format == "summary":
        return {
            "ai_answer": results["ai_answer"],
            "top_results": results["results"][:3],
        }

    return results
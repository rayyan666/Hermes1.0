import os
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

AI_ML_DOMAINS = [
    "arxiv.org",
    "huggingface.co",
    "paperswithcode.com",
    "github.com",
    "openai.com",
    "anthropic.com",
    "deepmind.google",
    "ai.googleblog.com",
    "bair.berkeley.edu",
    "blogs.microsoft.com",
    "towardsdatascience.com",
    "machinelearningmastery.com",
]


def hyper_search_aiml(query: str, depth: str = "advanced", max_results: int = 10) -> dict:
    """
    Deep search for AI/ML topics across top research sources.
    depth: "basic" (faster) or "advanced" (deeper, uses more API credits)
    """

    response = client.search(
        query=query,
        search_depth=depth,
        include_answer=True,
        include_raw_content=False,
        max_results=max_results,
        include_domains=AI_ML_DOMAINS,
    )

    results = [
        {
            "title": r.get("title"),
            "url": r.get("url"),
            "content": r.get("content"),
            "relevance_score": round(r.get("score", 0), 4),
            "published_date": r.get("published_date"),
        }
        for r in response.get("results", [])
    ]

    results.sort(key=lambda x: x["relevance_score"], reverse=True)

    return {
        "query": query,
        "ai_answer": response.get("answer"),
        "total_results": len(results),
        "results": results,
    }

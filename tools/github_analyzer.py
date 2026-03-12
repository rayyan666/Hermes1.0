import json
from services.github_service import (
    get_repo_overview,
    get_commit_activity,
    check_readme_quality,
    get_stale_repos,
    review_code,
    get_tech_stack,
    audit_dependencies,
    list_all_repos,
)
from services.claude_service import _get_groq_client, MODEL
from logger import get_logger

log = get_logger("github_analyzer")

VALID_ACTIONS = {
    "repo_overview",
    "commit_activity",
    "readme_quality",
    "stale_repos",
    "review_code",
    "tech_stack",
    "audit_dependencies",
    "list_repos",
}


def _strip_owner(repo: str | None) -> str | None:
    """
    Strip 'owner/' prefix from repo name if present.
    The UI sends 'rayyan666/REPO' but service functions only want 'REPO'.
    """
    if repo and "/" in repo:
        return repo.split("/", 1)[1]
    return repo


def _ai_insight(data: dict | list, prompt: str) -> str:
    """Run data through Groq for a concise AI summary."""
    try:
        client = _get_groq_client()
        full_prompt = f"{prompt}\n\nData:\n{json.dumps(data, indent=2)[:6000]}"
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": full_prompt}],
            max_tokens=800,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        log.warning(f"AI insight failed (returning raw data): {e}")
        return ""


def analyze_github(
    action: str,
    repo: str = None,
    file_path: str = None,
    days: int = 30,
    threshold_days: int = 180,
    include_private: bool = True,
    ai_summary: bool = True,
) -> dict:
    """
    Analyse your GitHub repositories with AI-powered insights.

    Actions:
      list_repos          — List all repos for the authenticated user (public + private)
      repo_overview       — List all repos with language, stars, activity status
      commit_activity     — Commit frequency over time across all or one repo
      readme_quality      — Score a repo README on key quality dimensions
      stale_repos         — Find repos with no recent activity
      review_code         — AI code review of a specific file
      tech_stack          — Full language and framework map across all repos
      audit_dependencies  — Check dependency files for unpinned packages

    Args:
        action:           One of the actions listed above
        repo:             Repo name e.g. "MAIL-MCP" or "rayyan666/MAIL-MCP" — both work
        file_path:        File path within repo — required for review_code
        days:             Lookback period for commit_activity (default 30)
        threshold_days:   Inactivity threshold for stale_repos (default 180)
        include_private:  Include private repos (default True)
        ai_summary:       Append an AI-generated insight to the result (default True)
    """
    log.info(f"analyze_github called | action={action} | repo={repo} | file={file_path}")

    if action not in VALID_ACTIONS:
        log.warning(f"Invalid action: {action}")
        return {
            "error": f"Unknown action '{action}'",
            "valid_actions": sorted(VALID_ACTIONS),
        }

    # Strip owner prefix — UI sends "owner/repo", service functions only want "repo"
    repo = _strip_owner(repo)

    # ── list_repos ────────────────────────────────────────────────────────────

    if action == "list_repos":
        repos = list_all_repos(include_private=include_private)
        return {"repos": repos}

    # ── Tier 1 ────────────────────────────────────────────────────────────────

    if action == "repo_overview":
        data = get_repo_overview(include_private=include_private)
        result = {
            "action": action,
            "total_repos": len(data),
            "active": sum(1 for r in data if r["status"] == "active"),
            "idle": sum(1 for r in data if r["status"] == "idle"),
            "stale": sum(1 for r in data if r["status"] == "stale"),
            "repos": data,
        }
        if ai_summary:
            result["ai_insight"] = _ai_insight(
                result,
                "You are a developer productivity assistant. Summarise this developer's GitHub portfolio in 3-4 sentences. "
                "Highlight their most active projects, primary language, and any patterns you notice. Be specific and direct."
            )
        return result

    if action == "commit_activity":
        data = get_commit_activity(days=days, repo_name=repo)
        result = {"action": action, **data}
        if ai_summary:
            result["ai_insight"] = _ai_insight(
                data,
                f"Analyse this developer's commit activity over the last {days} days. "
                "Comment on their consistency, most productive periods, "
                "and any gaps in activity. "
                "Give 2-3 specific observations. Be direct and practical."
            )
        return result

    if action == "readme_quality":
        if not repo:
            return {"error": "repo parameter is required for readme_quality"}
        data = check_readme_quality(repo_name=repo)
        result = {"action": action, **data}
        if ai_summary and data.get("has_readme"):
            result["ai_insight"] = _ai_insight(
                data,
                "You are a senior developer reviewing a README. Based on this quality report, "
                "give the top 3 most impactful improvements this developer should make. "
                "Be specific — name exact sections they should add or fix."
            )
        return result

    if action == "stale_repos":
        data = get_stale_repos(threshold_days=threshold_days)
        result = {"action": action, **data}
        if ai_summary and data["stale_repos"] > 0:
            result["ai_insight"] = _ai_insight(
                {"stale": data["stale"][:10]},
                "You are a developer productivity assistant. Looking at these stale repositories, "
                "suggest which ones are worth reviving, which should be archived, and why. "
                "Keep it to 3-4 sentences and be specific."
            )
        return result

    # ── Tier 2 ────────────────────────────────────────────────────────────────

    if action == "review_code":
        if not repo:
            return {"error": "repo parameter is required for review_code"}
        if not file_path:
            return {"error": "file_path parameter is required for review_code (e.g. 'services/gmail_service.py')"}

        data = review_code(repo_name=repo, file_path=file_path)
        result = {"action": action}
        result.update({k: v for k, v in data.items() if k != "content"})

        if ai_summary:
            review_prompt = (
                f"You are a senior Python developer doing a code review of '{file_path}'.\n"
                "Review this code and provide:\n"
                "1. Overall quality assessment (1-2 sentences)\n"
                "2. Top 3 specific issues or improvements (be precise — reference line numbers if possible)\n"
                "3. One thing done well\n"
                "4. Security concerns if any\n\n"
                f"Code:\n{data['content'][:4000]}"
            )
            try:
                client = _get_groq_client()
                response = client.chat.completions.create(
                    model=MODEL,
                    messages=[{"role": "user", "content": review_prompt}],
                    max_tokens=1000,
                )
                result["ai_code_review"] = response.choices[0].message.content.strip()
                log.info("AI code review generated successfully")
            except Exception as e:
                log.warning(f"AI code review failed: {e}")
                result["ai_code_review"] = "AI review unavailable"

        result["content"] = data["content"]
        return result

    if action == "tech_stack":
        data = get_tech_stack()
        result = {"action": action, **data}
        if ai_summary:
            result["ai_insight"] = _ai_insight(
                data,
                "You are a developer career advisor. Based on this developer's tech stack across all their repos, "
                "give 2-3 observations about their specialisation, and suggest one skill gap worth addressing "
                "based on current industry trends. Be specific and practical."
            )
        return result

    if action == "audit_dependencies":
        if not repo:
            return {"error": "repo parameter is required for audit_dependencies"}
        data = audit_dependencies(repo_name=repo)
        result = {"action": action, **data}
        if ai_summary and data.get("total_dependencies", 0) > 0:
            result["ai_insight"] = _ai_insight(
                {k: v for k, v in data.items() if k != "all_dependencies"},
                "You are a Python security and reliability expert. Based on this dependency audit, "
                "give 2-3 specific recommendations about dependency management best practices "
                "for this project. Be practical and direct."
            )
        return result

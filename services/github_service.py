"""
services/github_service.py — GitHub API wrapper
Handles all direct communication with the GitHub REST API via PyGithub.
"""

import os
from datetime import datetime, timezone, timedelta
from github import Github, GithubException
from dotenv import load_dotenv
from logger import get_logger

load_dotenv()
log = get_logger("github_service")

_client = None


def _get_client() -> Github:
    """Return authenticated GitHub client, initialising once."""
    global _client
    if _client:
        return _client

    token = os.getenv("GITHUB_TOKEN")
    if not token:
        log.error("GITHUB_TOKEN not set — add it to .env and claude_desktop_config.json")
        raise RuntimeError("GITHUB_TOKEN not set")

    _client = Github(token)
    user = _client.get_user()
    log.info(f"GitHub client authenticated as: {user.login}")
    return _client


# ── TIER 1 ────────────────────────────────────────────────────────────────────

def get_repo_overview(include_private: bool = True) -> list[dict]:
    """
    List all repos with language, stars, last push, and activity status.
    """
    log.info(f"Fetching repo overview | include_private={include_private}")
    g = _get_client()
    user = g.get_user()
    repos = [r for r in user.get_repos(type="all", sort="pushed", direction="desc")
             if r.owner.login == user.login]

    now = datetime.now(timezone.utc)

    result = []
    for repo in repos:
        if repo.private and not include_private:
            continue
        try:
            last_push = repo.pushed_at.replace(tzinfo=timezone.utc) if repo.pushed_at else None
            days_since = (now - last_push).days if last_push else None
            status = "active" if days_since and days_since < 30 else \
                     "idle" if days_since and days_since < 180 else "stale"

            result.append({
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description or "",
                "language": repo.language or "unknown",
                "stars": repo.stargazers_count,
                "forks": repo.forks_count,
                "private": repo.private,
                "last_pushed": last_push.strftime("%Y-%m-%d") if last_push else "never",
                "days_since_push": days_since,
                "status": status,
                "open_issues": repo.open_issues_count,
                "url": repo.html_url,
                "topics": repo.get_topics(),
            })
            log.debug(f"Repo: {repo.name} | {status} | {repo.language}")
        except GithubException as e:
            log.warning(f"Skipping repo {repo.name}: {e}")
            continue

    log.info(f"Fetched {len(result)} repos")
    return result


def get_commit_activity(days: int = 30, repo_name: str = None) -> dict:
    """
    Fetch commit activity across all repos or a specific repo.
    Returns daily counts, most active days, and per-repo breakdown.
    """
    log.info(f"Fetching commit activity | days={days} | repo={repo_name or 'all'}")
    g = _get_client()
    user = g.get_user()
    since = datetime.now(timezone.utc) - timedelta(days=days)

    repos = [g.get_repo(f"{user.login}/{repo_name}")] if repo_name \
            else [r for r in user.get_repos(type="all") if r.owner.login == user.login]

    daily_counts = {}
    repo_breakdown = {}
    total = 0

    for repo in repos:
        try:
            commits = repo.get_commits(author=user.login, since=since)
            count = 0
            for commit in commits:
                date_str = commit.commit.author.date.strftime("%Y-%m-%d")
                daily_counts[date_str] = daily_counts.get(date_str, 0) + 1
                count += 1
                total += 1
            if count > 0:
                repo_breakdown[repo.name] = count
            log.debug(f"{repo.name}: {count} commits in last {days} days")
        except GithubException as e:
            log.warning(f"Could not fetch commits for {repo.name}: {e}")
            continue

    most_active_day = max(daily_counts, key=daily_counts.get) if daily_counts else None
    sorted_daily = dict(sorted(daily_counts.items()))

    log.info(f"Total commits in last {days} days: {total}")
    return {
        "period_days": days,
        "total_commits": total,
        "repos_with_activity": len(repo_breakdown),
        "most_active_day": most_active_day,
        "most_active_day_count": daily_counts.get(most_active_day, 0) if most_active_day else 0,
        "daily_counts": sorted_daily,
        "repo_breakdown": dict(sorted(repo_breakdown.items(), key=lambda x: x[1], reverse=True)),
        "average_commits_per_day": round(total / days, 2),
    }


def check_readme_quality(repo_name: str) -> dict:
    """
    Fetch a repo's README and score it on key quality dimensions.
    Returns scores, findings, and specific improvement suggestions.
    """
    log.info(f"Checking README quality for: {repo_name}")
    g = _get_client()
    user = g.get_user()

    try:
        repo = g.get_repo(f"{user.login}/{repo_name}")
    except GithubException as e:
        log.error(f"Repo not found: {repo_name}: {e}")
        raise RuntimeError(f"Repository '{repo_name}' not found")

    try:
        readme = repo.get_readme()
        content = readme.decoded_content.decode("utf-8")
        log.debug(f"README fetched | length: {len(content)} chars")
    except GithubException:
        log.warning(f"No README found in {repo_name}")
        return {
            "repo": repo_name,
            "has_readme": False,
            "score": 0,
            "max_score": 100,
            "grade": "F",
            "findings": ["No README file found in this repository"],
            "suggestions": ["Create a README.md with at minimum a description, setup instructions, and usage examples"],
        }

    checks = {
        "has_description":      (10, "Project description present",          len(content) > 100),
        "has_installation":     (15, "Installation/setup instructions",      any(w in content.lower() for w in ["install", "setup", "getting started", "pip install", "npm install"])),
        "has_usage":            (15, "Usage examples or commands",           any(w in content.lower() for w in ["usage", "example", "how to", "run", "start"])),
        "has_code_blocks":      (10, "Code blocks present",                  "```" in content),
        "has_architecture":     (10, "Architecture or how it works section", any(w in content.lower() for w in ["architecture", "how it works", "overview", "design", "structure"])),
        "has_prerequisites":    (10, "Prerequisites listed",                 any(w in content.lower() for w in ["prerequisite", "requirements", "you will need", "before you begin", "python", "node"])),
        "has_contributing":     (5,  "Contributing guidelines",              any(w in content.lower() for w in ["contributing", "contribute", "pull request", "pr"])),
        "has_license":          (5,  "License mentioned",                    any(w in content.lower() for w in ["license", "mit", "apache", "gpl"])),
        "has_badges":           (5,  "Badges (CI, version, etc.)",           "![" in content and ("badge" in content.lower() or "shield" in content.lower() or "actions" in content.lower())),
        "adequate_length":      (10, "Adequate length (>500 chars)",         len(content) > 500),
        "has_screenshots":      (5,  "Screenshots or diagrams",              any(w in content.lower() for w in ["png", "jpg", "gif", "screenshot", "diagram", "!["])),
    }

    score = 0
    passed = []
    failed = []

    for key, (points, label, result) in checks.items():
        if result:
            score += points
            passed.append(f"{label} (+{points})")
        else:
            failed.append(f"Missing: {label} (-{points})")

    grade = "A" if score >= 85 else "B" if score >= 70 else "C" if score >= 55 else "D" if score >= 40 else "F"

    suggestions = []
    if not checks["has_installation"][2]:
        suggestions.append("Add a Setup or Installation section with step-by-step commands")
    if not checks["has_usage"][2]:
        suggestions.append("Add a Usage section with real example commands or screenshots")
    if not checks["has_code_blocks"][2]:
        suggestions.append("Wrap all commands and code in fenced code blocks (```)")
    if not checks["has_architecture"][2]:
        suggestions.append("Add an Architecture or How It Works section explaining the design")
    if not checks["has_badges"][2]:
        suggestions.append("Add CI status badge from GitHub Actions to show build health")
    if not checks["has_screenshots"][2]:
        suggestions.append("Add a screenshot or demo GIF — visual projects get far more attention")

    log.info(f"README quality for {repo_name}: {score}/100 ({grade})")
    return {
        "repo": repo_name,
        "has_readme": True,
        "score": score,
        "max_score": 100,
        "grade": grade,
        "readme_length_chars": len(content),
        "passed_checks": passed,
        "failed_checks": failed,
        "suggestions": suggestions,
    }


def get_stale_repos(threshold_days: int = 180) -> dict:
    """
    Find repos with no activity beyond threshold_days.
    Returns stale repos sorted by inactivity with actionable recommendations.
    """
    log.info(f"Scanning for stale repos | threshold={threshold_days} days")
    g = _get_client()
    user = g.get_user()
    repos = [r for r in user.get_repos(type="all") if r.owner.login == user.login]
    now = datetime.now(timezone.utc)

    stale = []
    active_count = 0
    total = 0

    for repo in repos:
        total += 1
        try:
            last_push = repo.pushed_at.replace(tzinfo=timezone.utc) if repo.pushed_at else None
            days_inactive = (now - last_push).days if last_push else 9999

            if days_inactive >= threshold_days:
                recommendation = "archive" if days_inactive > 365 else "review"
                stale.append({
                    "name": repo.name,
                    "url": repo.html_url,
                    "language": repo.language or "unknown",
                    "last_pushed": last_push.strftime("%Y-%m-%d") if last_push else "never",
                    "days_inactive": days_inactive,
                    "stars": repo.stargazers_count,
                    "has_readme": True,
                    "recommendation": recommendation,
                    "private": repo.private,
                })
                log.debug(f"Stale: {repo.name} — {days_inactive} days inactive")
            else:
                active_count += 1
        except GithubException as e:
            log.warning(f"Error checking {repo.name}: {e}")

    stale.sort(key=lambda x: x["days_inactive"], reverse=True)
    log.info(f"Found {len(stale)} stale repos out of {total} total")

    return {
        "total_repos": total,
        "active_repos": active_count,
        "stale_repos": len(stale),
        "threshold_days": threshold_days,
        "stale": stale,
        "summary": f"{len(stale)} of {total} repos have not been updated in {threshold_days}+ days",
    }


# ── TIER 2 ────────────────────────────────────────────────────────────────────

def review_code(repo_name: str, file_path: str) -> dict:
    """
    Fetch a file from a repo and prepare it for AI code review.
    Returns file content, metadata, and basic static analysis.
    """
    log.info(f"Fetching code for review | repo={repo_name} | file={file_path}")
    g = _get_client()
    user = g.get_user()

    try:
        repo = g.get_repo(f"{user.login}/{repo_name}")
    except GithubException as e:
        log.error(f"Repo not found: {repo_name}: {e}")
        raise RuntimeError(f"Repository '{repo_name}' not found")

    try:
        file_obj = repo.get_contents(file_path)
        content = file_obj.decoded_content.decode("utf-8")
        log.debug(f"File fetched | size: {len(content)} chars | sha: {file_obj.sha[:8]}")
    except GithubException as e:
        log.error(f"File not found: {file_path} in {repo_name}: {e}")
        raise RuntimeError(f"File '{file_path}' not found in '{repo_name}'")

    lines = content.splitlines()
    blank_lines = sum(1 for l in lines if l.strip() == "")
    comment_lines = sum(1 for l in lines if l.strip().startswith(("#", "//", "/*", "*", '"""', "'''")))
    long_lines = [i+1 for i, l in enumerate(lines) if len(l) > 120]

    log.info(f"Code fetched successfully | {len(lines)} lines")
    return {
        "repo": repo_name,
        "file_path": file_path,
        "language": file_path.rsplit(".", 1)[-1] if "." in file_path else "unknown",
        "total_lines": len(lines),
        "blank_lines": blank_lines,
        "comment_lines": comment_lines,
        "code_lines": len(lines) - blank_lines - comment_lines,
        "long_lines": long_lines[:10],
        "sha": file_obj.sha,
        "content": content,
    }


def get_tech_stack() -> dict:
    """
    Scan all repos and build a complete map of languages and frameworks used.
    """
    log.info("Building tech stack map across all repos")
    g = _get_client()
    user = g.get_user()
    repos = [r for r in user.get_repos(type="all") if r.owner.login == user.login]

    language_bytes = {}
    language_repos = {}
    framework_hints = {
        "Flask": ["flask", "requirements.txt"],
        "Django": ["django"],
        "FastAPI": ["fastapi"],
        "React": ["react", "package.json"],
        "Next.js": ["next", "next.config"],
        "Express": ["express"],
        "PyTorch": ["torch", "pytorch"],
        "TensorFlow": ["tensorflow"],
        "Pandas": ["pandas"],
        "Docker": ["dockerfile", "docker-compose"],
        "GitHub Actions": [".github/workflows"],
    }
    detected_frameworks = {}

    for repo in repos:
        try:
            langs = repo.get_languages()
            for lang, byte_count in langs.items():
                language_bytes[lang] = language_bytes.get(lang, 0) + byte_count
                if lang not in language_repos:
                    language_repos[lang] = []
                language_repos[lang].append(repo.name)

            try:
                contents = repo.get_contents("")
                file_names = [f.path.lower() for f in contents]
                for framework, keywords in framework_hints.items():
                    if any(any(kw in fn for fn in file_names) for kw in keywords):
                        if framework not in detected_frameworks:
                            detected_frameworks[framework] = []
                        detected_frameworks[framework].append(repo.name)
            except GithubException:
                pass

            log.debug(f"Scanned: {repo.name}")
        except GithubException as e:
            log.warning(f"Could not scan {repo.name}: {e}")
            continue

    total_bytes = sum(language_bytes.values()) or 1
    language_percentages = {
        lang: round(bytes_ / total_bytes * 100, 1)
        for lang, bytes_ in sorted(language_bytes.items(), key=lambda x: x[1], reverse=True)
    }

    primary_language = max(language_bytes, key=language_bytes.get) if language_bytes else "unknown"
    log.info(f"Tech stack scanned | {len(language_percentages)} languages | primary: {primary_language}")

    return {
        "total_repos_scanned": len(repos),
        "primary_language": primary_language,
        "language_breakdown": language_percentages,
        "language_repo_count": {lang: len(rlist) for lang, rlist in language_repos.items()},
        "detected_frameworks": detected_frameworks,
        "total_languages_used": len(language_percentages),
    }


def audit_dependencies(repo_name: str) -> dict:
    """
    Fetch dependency files from a repo and check for known outdated packages.
    Supports requirements.txt, package.json, Pipfile.
    """
    log.info(f"Auditing dependencies for: {repo_name}")
    g = _get_client()
    user = g.get_user()

    try:
        repo = g.get_repo(f"{user.login}/{repo_name}")
    except GithubException as e:
        log.error(f"Repo not found: {repo_name}: {e}")
        raise RuntimeError(f"Repository '{repo_name}' not found")

    dep_files = {
        "requirements.txt": "python",
        "Pipfile": "python",
        "package.json": "javascript",
        "pyproject.toml": "python",
        "Gemfile": "ruby",
    }

    found = {}
    for filename, ecosystem in dep_files.items():
        try:
            file_obj = repo.get_contents(filename)
            content = file_obj.decoded_content.decode("utf-8")
            found[filename] = {
                "ecosystem": ecosystem,
                "content": content,
                "line_count": len(content.splitlines()),
            }
            log.debug(f"Found dependency file: {filename}")
        except GithubException:
            continue

    if not found:
        log.warning(f"No dependency files found in {repo_name}")
        return {
            "repo": repo_name,
            "dependency_files_found": [],
            "total_dependencies": 0,
            "message": "No recognised dependency files found (requirements.txt, package.json, etc.)",
        }

    all_deps = []
    for filename, info in found.items():
        if filename == "requirements.txt":
            for line in info["content"].splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    parts = line.replace("==", "=").replace(">=", "=").replace("<=", "=").split("=")
                    name = parts[0].strip()
                    version = parts[1].strip() if len(parts) > 1 else "unpinned"
                    all_deps.append({
                        "name": name,
                        "version": version,
                        "file": filename,
                        "ecosystem": info["ecosystem"],
                        "pinned": "==" in line,
                    })

    unpinned = [d for d in all_deps if not d["pinned"] and d["ecosystem"] == "python"]
    pinned = [d for d in all_deps if d["pinned"]]

    log.info(f"Dependency audit complete | {len(all_deps)} packages | {len(unpinned)} unpinned")
    return {
        "repo": repo_name,
        "dependency_files_found": list(found.keys()),
        "total_dependencies": len(all_deps),
        "pinned_count": len(pinned),
        "unpinned_count": len(unpinned),
        "unpinned_packages": [d["name"] for d in unpinned],
        "all_dependencies": all_deps,
        "recommendation": "All dependencies pinned — good for reproducibility." if not unpinned
                          else f"{len(unpinned)} unpinned packages found. Consider pinning versions for reproducible builds.",
    }


def list_all_repos(include_private: bool = True) -> list:
    """Return all repos owned by the authenticated user, sorted by last push date."""
    g = _get_client()
    user = g.get_user()  # authenticated user — sees private repos
    repos = []
    for r in user.get_repos(type="all", sort="pushed", direction="desc"):
        if r.owner.login != user.login:
            continue  # skip org repos and forks not owned by user
        if r.private and not include_private:
            continue
        repos.append({
            "name": r.name,
            "full_name": r.full_name,
            "private": r.private,
            "language": r.language,
            "stargazers_count": r.stargazers_count,
            "forks_count": r.forks_count,
            "description": r.description,
            "pushed_at": str(r.pushed_at)[:10] if r.pushed_at else None,
        })
    log.info(f"list_all_repos: returned {len(repos)} repos (include_private={include_private})")
    return repos
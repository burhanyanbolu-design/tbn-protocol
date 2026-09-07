"""SEO basics: sitemap.xml + robots.txt.
Host-aware — serves the right domain + page set depending on which
hostname the request came in on (certify.hardinai.co.uk, tbn.hardinai.co.uk).
(c) 2026 Hardin Enterprises Ltd."""
from flask import Blueprint, Response, request
from datetime import datetime, timezone

seo = Blueprint("seo", __name__)

TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")

SITE_CONFIG = {
    "certify": {
        "domain": "https://certify.hardinai.co.uk",
        "pages": [
            ("/", "1.0", "weekly"),
            ("/article50", "1.0", "weekly"),
            ("/certify-full", "0.8", "monthly"),
            ("/memory", "0.7", "monthly"),
        ],
    },
    "tbn": {
        "domain": "https://tbn.hardinai.co.uk",
        "pages": [
            ("/", "1.0", "weekly"),
            ("/sentinel", "0.9", "weekly"),
            ("/tracer", "0.6", "monthly"),
        ],
        "disallow": ["/console", "/dashboard", "/login", "/api/"],
    },
    "knowmyresults": {
        "domain": "https://knowmyresults.com",
        "pages": [
            ("/", "1.0", "weekly"),
        ],
    },
    "memory": {
        "domain": "https://memory.hardinai.co.uk",
        "pages": [
            ("/", "1.0", "weekly"),
            ("/memory/terms", "0.3", "monthly"),
        ],
    },
    "haso": {
        "domain": "https://haso.hardinai.co.uk",
        "pages": [
            ("/", "1.0", "weekly"),
        ],
        "disallow": ["/agent-security/enquiries", "/api/"],
    },
}

DEFAULT_SITE = "certify"


def _resolve_site():
    # This is the single source of truth for every domain's robots.txt /
    # sitemap.xml. A second, now-unreachable copy of this host-check used to
    # live in health_agent.py — Flask only ever calls ONE view function per
    # URL rule (whichever blueprint registers first), so that copy's
    # knowmyresults/memory branches never actually ran. Every request fell
    # through to this function's old default ("certify") regardless of host.
    # Real-world impact: knowmyresults.com served certify.hardinai.co.uk's
    # sitemap in robots.txt, which is a genuine indexing problem — crawlers
    # were being pointed at the wrong domain's sitemap entirely. Fixed by
    # making this the one place that knows about every domain (removed the
    # dead duplicate in health_agent.py).
    host = (request.host or "").lower()
    if "haso.hardinai" in host:
        return SITE_CONFIG["haso"]
    if "tbn.hardinai" in host:
        return SITE_CONFIG["tbn"]
    if "knowmyresults" in host:
        return SITE_CONFIG["knowmyresults"]
    if "memory.hardinai" in host:
        return SITE_CONFIG["memory"]
    return SITE_CONFIG[DEFAULT_SITE]


@seo.route("/sitemap.xml")
def sitemap():
    site = _resolve_site()
    domain = site["domain"]
    urls = ""
    for path, priority, freq in site["pages"]:
        urls += (
            f"  <url>\n"
            f"    <loc>{domain}{path}</loc>\n"
            f"    <lastmod>{TODAY}</lastmod>\n"
            f"    <changefreq>{freq}</changefreq>\n"
            f"    <priority>{priority}</priority>\n"
            f"  </url>\n"
        )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f'{urls}'
        '</urlset>'
    )
    return Response(xml, mimetype="application/xml")


@seo.route("/robots.txt")
def robots():
    site = _resolve_site()
    domain = site["domain"]
    disallow = site.get("disallow", [])
    lines = ["User-agent: *", "Allow: /"]
    for path in disallow:
        lines.append(f"Disallow: {path}")
    lines.append("")
    lines.append(f"Sitemap: {domain}/sitemap.xml")
    lines.append("")
    return Response("\n".join(lines), mimetype="text/plain")

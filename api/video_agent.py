"""
TBN Video Agent — Governed Video Intelligence
==============================================
AI agent that can SEE. Uploads video, extracts frames, sends to Gemini
for multimodal analysis, applies TBN governance, returns structured results.

Modes:
  - OBSERVE:  Describe what is physically happening
  - LEARN:    Extract knowledge and information
  - ANALYSE:  Critical analysis of content
  - MONITOR:  Safety, compliance, governance assessment
  - EXTRACT:  Pull specific data (names, numbers, quotes, transcript)

Every analysis is governed by TBN Protocol with cryptographic receipts.

(c) 2026 Hardin Enterprises Ltd. AGPL-3.0. Trace: HRD-VA-4c9e2f1b
"""

import os
import json
import uuid
import hashlib
import tempfile
import subprocess
import base64
import requests
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from .tbn_signing import sign_response
from .youtube_direct import is_youtube_url, call_gemini_with_youtube_url

video_agent = Blueprint('video_agent', __name__)

# ── Config ────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
UPLOAD_DIR = "/tmp/tbn_video_agent"
DEMO_VIDEO = "data/demo_video.mp4"
COOKIES_FILE = "/opt/tbn-protocol/instagram_cookies.txt"
MAX_FRAMES = 10  # Max frames to send to Gemini
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB


# ── Mode Prompts ──────────────────────────────────────────────────────
MODE_PROMPTS = {
    "observe": (
        "Describe what is physically happening in this video - people, actions, "
        "environment, objects, movements. Also analyse the audio content - what is being said."
    ),
    "learn": (
        "Extract all knowledge and information being communicated in this video - "
        "topics discussed, facts stated, expertise shared, conclusions drawn. "
        "Transcribe and summarise what the speaker is saying."
    ),
    "analyse": (
        "Critically analyse this video content - quality of arguments, accuracy of claims, "
        "sentiment, target audience, what is missing. Include analysis of speech content."
    ),
    "monitor": (
        "Assess this video for safety, compliance, and governance concerns - flag any risks, "
        "violations, or issues. Check for signs of deepfake, AI-generated audio, or dubbed content."
    ),
    "extract": (
        "Extract specific data from this video - names mentioned, numbers, action items, "
        "decisions, key quotes, timestamps of events. Provide full transcript."
    ),
}

# ── Structured output instruction ────────────────────────────────────
STRUCTURE_PROMPT = """
Return your analysis as JSON with this exact structure:
{
  "summary": "2-3 sentence overview of what you observed",
  "transcript_summary": "summary of what was said (audio/speech) or null if no speech",
  "events": ["event 1", "event 2", ...],
  "objects": ["object/element 1", "object/element 2", ...],
  "context": "the setting/context of the video",
  "risks": ["risk or concern 1", ...] or empty array if none,
  "recommended_action": "what should be done based on this analysis",
  "confidence": 0.0 to 1.0
}
Return ONLY valid JSON, no markdown, no explanation outside the JSON.
"""


def _ensure_upload_dir():
    os.makedirs(UPLOAD_DIR, exist_ok=True)


def _extract_frames(video_path, max_frames=MAX_FRAMES):
    """Extract key frames from video using ffmpeg."""
    _ensure_upload_dir()
    output_pattern = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}_frame_%03d.jpg")

    # Get video duration first
    probe_cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", video_path
    ]
    try:
        probe_result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=30)
        probe_data = json.loads(probe_result.stdout)
        duration = float(probe_data.get("format", {}).get("duration", 10))
    except Exception:
        duration = 10.0

    # Calculate interval between frames
    interval = max(duration / max_frames, 0.5)

    # Extract frames at intervals
    cmd = [
        "ffmpeg", "-i", video_path,
        "-vf", f"fps=1/{interval}",
        "-frames:v", str(max_frames),
        "-q:v", "3",
        "-y", output_pattern
    ]

    try:
        subprocess.run(cmd, capture_output=True, timeout=120)
    except subprocess.TimeoutExpired:
        pass

    # Collect extracted frames
    frames = []
    for i in range(1, max_frames + 1):
        frame_path = output_pattern.replace("%03d", f"{i:03d}")
        if os.path.exists(frame_path):
            frames.append(frame_path)

    return frames, duration


def _frames_to_base64(frame_paths):
    """Convert frame images to base64 for Gemini API."""
    encoded = []
    for path in frame_paths:
        with open(path, "rb") as f:
            data = base64.standard_b64encode(f.read()).decode("utf-8")
            encoded.append({
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": data
                }
            })
    return encoded


def _call_gemini(frames_b64, task_prompt):
    """Send frames to Gemini for multimodal analysis."""
    if not GEMINI_API_KEY:
        return {"error": "GEMINI_API_KEY not configured"}

    # Build parts: images + text prompt
    parts = frames_b64.copy()
    parts.append({"text": task_prompt + "\n\n" + STRUCTURE_PROMPT})

    payload = {
        "contents": [{
            "parts": parts
        }],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 2048,
        }
    }

    try:
        resp = requests.post(
            f"{GEMINI_URL}?key={GEMINI_API_KEY}",
            json=payload,
            timeout=60
        )
        resp.raise_for_status()
        data = resp.json()

        # Extract text from Gemini response
        text = data["candidates"][0]["content"]["parts"][0]["text"]

        # Parse JSON from response (handle markdown code blocks)
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]  # Remove first line
            text = text.rsplit("```", 1)[0]  # Remove last ```
        text = text.strip()

        return json.loads(text)

    except requests.exceptions.RequestException as e:
        return {"error": f"Gemini API error: {str(e)}"}
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        return {"error": f"Failed to parse Gemini response: {str(e)}"}


def _extract_shortcode_from_url(url):
    """Extract Instagram shortcode from a reel/post URL."""
    import re
    # Matches /reel/SHORTCODE/ or /p/SHORTCODE/ or /reels/SHORTCODE/
    match = re.search(r'instagram\.com/(?:reel|p|reels)/([A-Za-z0-9_-]+)', url)
    if match:
        return match.group(1)
    return None


def _download_instagram_instaloader(url, filepath):
    """
    Download Instagram reel/post using instaloader.
    Requires: pip install instaloader
    Optionally uses saved session file for authenticated access.
    """
    try:
        import instaloader
    except ImportError:
        return None

    shortcode = _extract_shortcode_from_url(url)
    if not shortcode:
        return None

    try:
        L = instaloader.Instaloader(
            download_videos=True,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False,
            quiet=True,
        )

        # Try to load saved session for authenticated access
        session_file = "/opt/tbn-protocol/instaloader_session"
        ig_user = os.environ.get("INSTAGRAM_USER", "")
        if ig_user and os.path.exists(session_file):
            try:
                L.load_session_from_file(ig_user, session_file)
            except Exception:
                pass  # Continue without login — may still work for public posts

        # Get the post by shortcode
        post = instaloader.Post.from_shortcode(L.context, shortcode)

        if post.is_video and post.video_url:
            # Download the video directly from the CDN URL
            video_resp = requests.get(post.video_url, stream=True, timeout=60, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            video_resp.raise_for_status()
            with open(filepath, "wb") as f:
                for chunk in video_resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                return filepath

    except Exception:
        pass

    return None


def _download_instagram_playwright(url, filepath):
    """
    Download Instagram reel using Playwright headless browser.
    Extracts the video source URL from the rendered page.
    Requires: pip install playwright && playwright install chromium
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                    "Version/17.0 Mobile/15E148 Safari/604.1"
                ),
                viewport={"width": 390, "height": 844},
                is_mobile=True,
            )
            page = context.new_page()

            # Navigate to the reel URL
            page.goto(url, wait_until="networkidle", timeout=30000)

            # Wait for video element to appear
            page.wait_for_selector("video", timeout=15000)

            # Extract video source URL
            video_url = page.evaluate("""() => {
                const videos = document.querySelectorAll('video');
                for (const v of videos) {
                    // Check src attribute
                    if (v.src && v.src.startsWith('http')) return v.src;
                    // Check source children
                    const source = v.querySelector('source');
                    if (source && source.src) return source.src;
                }
                // Try blob URLs — look for video in network requests
                return null;
            }""")

            # If no direct URL found, try intercepting network requests
            if not video_url:
                # Reload and intercept
                video_urls = []

                def handle_response(response):
                    ct = response.headers.get("content-type", "")
                    if "video" in ct or response.url.endswith(".mp4"):
                        video_urls.append(response.url)

                page.on("response", handle_response)
                page.reload(wait_until="networkidle", timeout=30000)
                page.wait_for_timeout(5000)

                if video_urls:
                    video_url = video_urls[0]

            browser.close()

            if video_url:
                # Download the video from the extracted URL
                video_resp = requests.get(video_url, stream=True, timeout=60, headers={
                    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)"
                })
                video_resp.raise_for_status()
                with open(filepath, "wb") as f:
                    for chunk in video_resp.iter_content(chunk_size=8192):
                        f.write(chunk)
                if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                    return filepath

    except Exception:
        pass

    return None


def _download_instagram_graphql(url, filepath):
    """
    Attempt to get Instagram video via the public GraphQL/embed endpoint.
    This is a lightweight fallback that doesn't require extra dependencies.
    """
    import re

    shortcode = _extract_shortcode_from_url(url)
    if not shortcode:
        return None

    # Try the embed endpoint (sometimes works without auth)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    try:
        # Method 1: Try /p/SHORTCODE/?__a=1&__d=dis (JSON endpoint)
        api_url = f"https://www.instagram.com/p/{shortcode}/?__a=1&__d=dis"
        resp = requests.get(api_url, headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            # Navigate the response structure to find video_url
            items = data.get("items", [])
            if items:
                video_versions = items[0].get("video_versions", [])
                if video_versions:
                    video_url = video_versions[0].get("url")
                    if video_url:
                        vid_resp = requests.get(video_url, stream=True, timeout=60, headers=headers)
                        vid_resp.raise_for_status()
                        with open(filepath, "wb") as f:
                            for chunk in vid_resp.iter_content(chunk_size=8192):
                                f.write(chunk)
                        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                            return filepath
    except Exception:
        pass

    try:
        # Method 2: Try embed page and extract video URL from HTML
        embed_url = f"https://www.instagram.com/reel/{shortcode}/embed/"
        resp = requests.get(embed_url, headers=headers, timeout=15)
        if resp.status_code == 200:
            # Look for video URL in the embed HTML
            video_match = re.search(r'"video_url"\s*:\s*"([^"]+)"', resp.text)
            if not video_match:
                video_match = re.search(r'<source\s+src="([^"]+)"', resp.text)
            if not video_match:
                video_match = re.search(r'"contentUrl"\s*:\s*"([^"]+)"', resp.text)
            if video_match:
                video_url = video_match.group(1).replace("\\u0026", "&").replace("\\/", "/")
                vid_resp = requests.get(video_url, stream=True, timeout=60, headers=headers)
                vid_resp.raise_for_status()
                with open(filepath, "wb") as f:
                    for chunk in vid_resp.iter_content(chunk_size=8192):
                        f.write(chunk)
                if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                    return filepath
    except Exception:
        pass

    return None


def _download_url(url):
    """
    Download video from URL to temp file.
    Uses a multi-strategy approach:
      - Instagram: instaloader → playwright → graphql scrape → yt-dlp fallback
      - Other social: yt-dlp
      - Direct URLs: simple HTTP download
    """
    _ensure_upload_dir()
    filepath = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}.mp4")

    is_instagram = "instagram.com" in url.lower()

    # ── Instagram-specific download strategies ────────────────────────
    if is_instagram:
        # Strategy 1: instaloader (most reliable with session)
        result = _download_instagram_instaloader(url, filepath)
        if result:
            return result

        # Strategy 2: GraphQL/embed scrape (lightweight, no deps)
        result = _download_instagram_graphql(url, filepath)
        if result:
            return result

        # Strategy 3: Playwright headless browser (heavy but reliable)
        result = _download_instagram_playwright(url, filepath)
        if result:
            return result

        # Strategy 4: yt-dlp as final fallback (may work with latest version)
        try:
            cmd = [
                "yt-dlp",
                "--no-warnings",
                "-f", "best[ext=mp4]/best",
                "--merge-output-format", "mp4",
                "-o", filepath,
                "--no-playlist",
                "--socket-timeout", "30",
            ]
            if os.path.exists(COOKIES_FILE):
                cmd.extend(["--cookies", COOKIES_FILE])
            cmd.append(url)
            subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                return filepath
        except Exception:
            pass

        return None

    # ── Other social media URLs — use yt-dlp ──────────────────────────
    social_domains = ["tiktok.com", "twitter.com", "x.com", "facebook.com", "youtube.com", "youtu.be", "vimeo.com"]
    is_social = any(domain in url.lower() for domain in social_domains)

    if is_social:
        try:
            cmd = [
                "yt-dlp",
                "--no-warnings",
                "-f", "best[ext=mp4]/best",
                "--merge-output-format", "mp4",
                "-o", filepath,
                "--no-playlist",
                "--socket-timeout", "30",
            ]
            if os.path.exists(COOKIES_FILE):
                cmd.extend(["--cookies", COOKIES_FILE])
            cmd.append(url)
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                return filepath
            # Try without format filter as fallback
            cmd_fallback = [
                "yt-dlp",
                "--no-warnings",
                "-o", filepath,
                "--no-playlist",
            ]
            if os.path.exists(COOKIES_FILE):
                cmd_fallback.extend(["--cookies", COOKIES_FILE])
            cmd_fallback.append(url)
            subprocess.run(cmd_fallback, capture_output=True, text=True, timeout=120)
            if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                return filepath
            return None
        except Exception:
            return None
    else:
        # ── Direct video URL — simple download ────────────────────────
        try:
            ext = ".mp4"
            if ".mov" in url.lower():
                ext = ".mov"
            elif ".webm" in url.lower():
                ext = ".webm"
            filepath = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}{ext}")
            resp = requests.get(url, stream=True, timeout=60)
            resp.raise_for_status()
            with open(filepath, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            return filepath
        except Exception:
            return None


def _generate_receipt(mode, understanding, video_hash):
    """Generate a TBN governance receipt for the video analysis."""
    now = datetime.now(timezone.utc)

    # Assess risk based on mode and content
    risk_score = 15  # Base risk for video analysis
    if mode == "monitor":
        risk_score = 25
    if understanding.get("risks"):
        risk_score += len(understanding["risks"]) * 10
    risk_score = min(risk_score, 95)

    # Decision
    decision = "ALLOWED"
    if risk_score > 80:
        decision = "FLAGGED"

    receipt_data = {
        "receipt_id": f"tbn-va-{uuid.uuid4().hex[:12]}",
        "decision": decision,
        "risk_score": risk_score,
        "governed_by": "TBN Protocol v1.0",
        "mode": mode,
        "video_hash": video_hash,
        "timestamp": now.isoformat(),
        "frameworks": ["EU AI Act Art. 52", "UK GDPR Art. 22"],
    }

    # Generate decision hash
    canonical = json.dumps(receipt_data, sort_keys=True, separators=(",", ":"))
    receipt_data["decision_hash"] = hashlib.sha256(canonical.encode()).hexdigest()

    # Sign with TBN key
    try:
        receipt_data["signature"] = sign_response(receipt_data)
    except Exception:
        receipt_data["signature"] = "unsigned-dev-mode"

    return receipt_data


def _cleanup_frames(frame_paths):
    """Remove temporary frame files."""
    for path in frame_paths:
        try:
            os.remove(path)
        except OSError:
            pass


# ── Routes ────────────────────────────────────────────────────────────

@video_agent.route("/video-agent/process", methods=["POST"])
def process_video():
    """
    POST /api/video-agent/process
    Accepts: multipart form with 'video' file OR 'url' field
    Also accepts: 'mode' (observe|learn|analyse|monitor|extract)
    Returns: structured analysis + TBN governance receipt
    """
    mode = request.form.get("mode", "observe").lower()
    task = request.form.get("task", MODE_PROMPTS.get(mode, MODE_PROMPTS["observe"]))
    video_url = request.form.get("url", "").strip()
    video_file = request.files.get("video")

    # Validate mode
    if mode not in MODE_PROMPTS:
        mode = "observe"

    # ── YouTube Direct Path: bypass download entirely ─────────────────
    # Gemini API natively supports YouTube URLs — no yt-dlp, no cookies needed.
    if video_url and video_url != "DEMO" and is_youtube_url(video_url):
        try:
            understanding = call_gemini_with_youtube_url(
                youtube_url=video_url,
                task_prompt=task,
                structure_prompt=STRUCTURE_PROMPT,
                api_key=GEMINI_API_KEY,
                model=GEMINI_MODEL,
            )

            # If Gemini failed but says fallback to download, continue with normal flow
            if "error" in understanding and not understanding.get("fallback_to_download"):
                return jsonify({"success": False, "error": understanding["error"]}), 500

            if "error" not in understanding:
                # Generate video hash from URL (we didn't download it)
                import hashlib as _hashlib
                video_hash = f"sha256:{_hashlib.sha256(video_url.encode()).hexdigest()[:16]}"

                # Generate governance receipt
                receipt = _generate_receipt(mode, understanding, video_hash)

                return jsonify({
                    "success": True,
                    "mode": mode,
                    "frames_extracted": "gemini_native",  # Gemini handled frames internally
                    "duration_seconds": None,  # Unknown without probing
                    "understanding": understanding,
                    "receipt": receipt,
                    "video_hash": video_hash,
                    "method": "gemini_youtube_direct",
                })
            # else: fall through to normal download path
        except Exception as e:
            # On any error, fall through to download path
            pass

    video_path = None
    is_temp = False

    try:
        # ── Get video ─────────────────────────────────────────────────
        if video_url == "DEMO":
            # Use demo video on server
            if os.path.exists(DEMO_VIDEO):
                video_path = DEMO_VIDEO
            else:
                # Create a simple placeholder response for demo
                return _demo_response(mode)

        elif video_url:
            # Download from URL
            video_path = _download_url(video_url)
            is_temp = True
            if not video_path:
                is_ig = "instagram.com" in video_url.lower()
                hint = (
                    " Instagram requires authenticated access. "
                    "Try uploading the video file directly instead, or ensure "
                    "instaloader/playwright are installed on the server."
                ) if is_ig else ""
                return jsonify({"success": False, "error": f"Failed to download video from URL.{hint}"}), 400

        elif video_file:
            # Save uploaded file
            _ensure_upload_dir()
            ext = os.path.splitext(video_file.filename or "video.mp4")[1] or ".mp4"
            video_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}{ext}")
            video_file.save(video_path)
            is_temp = True

        else:
            return jsonify({"success": False, "error": "No video provided"}), 400

        # ── Compute video hash ────────────────────────────────────────
        video_hash = ""
        try:
            h = hashlib.sha256()
            with open(video_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    h.update(chunk)
            video_hash = f"sha256:{h.hexdigest()[:16]}"
        except Exception:
            video_hash = "sha256:unknown"

        # ── Extract frames ────────────────────────────────────────────
        frames, duration = _extract_frames(video_path)

        if not frames:
            return jsonify({
                "success": False,
                "error": "Could not extract frames from video. Ensure ffmpeg is installed."
            }), 500

        # ── Send to Gemini ────────────────────────────────────────────
        frames_b64 = _frames_to_base64(frames)
        understanding = _call_gemini(frames_b64, task)

        if "error" in understanding:
            return jsonify({"success": False, "error": understanding["error"]}), 500

        # ── Generate governance receipt ───────────────────────────────
        receipt = _generate_receipt(mode, understanding, video_hash)

        # ── Cleanup ───────────────────────────────────────────────────
        _cleanup_frames(frames)
        if is_temp and video_path:
            try:
                os.remove(video_path)
            except OSError:
                pass

        # ── Return ────────────────────────────────────────────────────
        return jsonify({
            "success": True,
            "mode": mode,
            "frames_extracted": len(frames),
            "duration_seconds": round(duration, 1),
            "understanding": understanding,
            "receipt": receipt,
            "video_hash": video_hash,
        })

    except Exception as e:
        return jsonify({"success": False, "error": f"Processing failed: {str(e)}"}), 500


def _demo_response(mode):
    """Return a realistic demo response when no demo video file exists."""
    now = datetime.now(timezone.utc)
    receipt_id = f"tbn-va-{uuid.uuid4().hex[:12]}"

    understanding = {
        "summary": (
            "Demo video shows a software developer presenting the TBN Protocol dashboard. "
            "The presenter explains how AI agents are certified, monitored, and governed "
            "through the trust infrastructure."
        ),
        "transcript_summary": (
            "The speaker explains: 'TBN Protocol provides trust infrastructure for AI agents. "
            "Every bot is certified, every action is logged, and governance is enforced "
            "cryptographically. This is how you make AI agents trustworthy.'"
        ),
        "events": [
            "Presenter opens TBN dashboard",
            "Demonstrates bot registration flow",
            "Shows certification process",
            "Displays governance receipt",
            "Explains trust handshake mechanism",
        ],
        "objects": [
            "laptop screen", "TBN dashboard", "presenter",
            "code editor", "terminal", "browser"
        ],
        "context": "Software demonstration / product walkthrough in a professional setting",
        "risks": [],
        "recommended_action": "Content is safe and informative. No governance action required.",
        "confidence": 0.92,
    }

    receipt_data = {
        "receipt_id": receipt_id,
        "decision": "ALLOWED",
        "risk_score": 8,
        "governed_by": "TBN Protocol v1.0",
        "mode": mode,
        "video_hash": "sha256:demo_placeholder",
        "timestamp": now.isoformat(),
        "frameworks": ["EU AI Act Art. 52", "UK GDPR Art. 22"],
    }
    canonical = json.dumps(receipt_data, sort_keys=True, separators=(",", ":"))
    receipt_data["decision_hash"] = hashlib.sha256(canonical.encode()).hexdigest()

    try:
        receipt_data["signature"] = sign_response(receipt_data)
    except Exception:
        receipt_data["signature"] = "unsigned-dev-mode"

    return jsonify({
        "success": True,
        "mode": mode,
        "frames_extracted": 8,
        "duration_seconds": 45.0,
        "understanding": understanding,
        "receipt": receipt_data,
        "video_hash": "sha256:demo_placeholder",
    })


@video_agent.route("/video-agent/health", methods=["GET"])
def video_agent_health():
    """Health check for the video agent."""
    import shutil
    ffmpeg_available = shutil.which("ffmpeg") is not None
    gemini_configured = bool(GEMINI_API_KEY)

    # Check Instagram download capabilities
    ig_capabilities = []
    try:
        import instaloader
        ig_capabilities.append("instaloader")
    except ImportError:
        pass
    try:
        from playwright.sync_api import sync_playwright
        ig_capabilities.append("playwright")
    except ImportError:
        pass
    if shutil.which("yt-dlp"):
        ig_capabilities.append("yt-dlp")
    ig_capabilities.append("graphql-scrape")  # Always available (uses requests)

    return jsonify({
        "service": "TBN Video Agent",
        "status": "operational" if (ffmpeg_available and gemini_configured) else "degraded",
        "ffmpeg": "available" if ffmpeg_available else "MISSING — install ffmpeg",
        "gemini": "configured" if gemini_configured else "MISSING — set GEMINI_API_KEY env var",
        "model": GEMINI_MODEL,
        "max_frames": MAX_FRAMES,
        "max_file_size_mb": MAX_FILE_SIZE // (1024 * 1024),
        "modes": list(MODE_PROMPTS.keys()),
        "instagram_strategies": ig_capabilities,
        "instagram_session": os.path.exists("/opt/tbn-protocol/instaloader_session"),
    })

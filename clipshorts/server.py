"""MCP server: exposes the clipper to Claude (or any MCP client) over stdio."""
try:  # mcp >= 2.0
    from mcp.server.mcpserver import MCPServer
except ImportError:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP as MCPServer

from . import doctor as _doctor
from . import pipeline, tracker, youtube

mcp = MCPServer("clipper")


@mcp.tool()
def make_clips(source: str, n: int = 8, min_score: float = 60, layout: str = "blur",
               whisper_model: str = "small") -> dict:
    """Clip a long video (URL or local path) the user has permission to use into up to n
    captioned 9:16 Shorts. Returns a report with virality_score (0-100) and verdict per clip.
    layout: blur (safe default) | zoom (podcasts; follows the face) | crop (single centered speaker)
    | face (full-bleed crop that follows the speaker's face, centered if none is found).
    Long videos take minutes; transcripts are cached so re-runs are fast."""
    return pipeline.make_clips(source, n, min_score, layout, whisper_model, log=lambda *_: None)


@mcp.tool()
def rerender_clip(folder: str, clip_id: int, hook: str = "", layout: str | None = None) -> dict:
    """Re-render one clip from a report, e.g. adding a hook banner at the top (keep it <= 6 words)
    or switching layout (blur | zoom | crop | face)."""
    return pipeline.rerender(folder, clip_id, hook, layout)


@mcp.tool()
def list_reports() -> list:
    """All clip reports generated so far."""
    return pipeline.list_reports()


@mcp.tool()
def next_post_slots(n: int = 4) -> list:
    """Next n posting slots (9:00/13:00/18:00/21:00 local) as RFC3339 UTC for publish_at."""
    return youtube.next_slots(n)


@mcp.tool()
def upload_short(path: str, title: str, description: str = "", tags: list[str] | None = None,
                 publish_at: str | None = None, campaign: str = "") -> str:
    """Upload a clip to the user's YouTube channel. Only call after the user approved this exact
    clip and title. publish_at (RFC3339 UTC) schedules it. Returns the Shorts URL."""
    url = youtube.upload(path, title, description, tags, publish_at)
    tracker.log(url, 0, campaign, clip=path, note="uploaded")
    return url


@mcp.tool()
def log_views(url: str, views: int, campaign: str = "", note: str = "") -> dict:
    """Record the current view count of a posted clip (any platform)."""
    return tracker.log(url, views, campaign, note=note)


@mcp.tool()
def stats() -> dict:
    """Views and estimated earnings per campaign, plus top posts."""
    return tracker.stats()


@mcp.tool()
def doctor() -> dict:
    """Check that dependencies and YouTube credentials are set up."""
    return _doctor.doctor()

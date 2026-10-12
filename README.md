# clip-shorts ✂️

**Free, local auto-clipper for YouTube Shorts, built for Claude Code.**
Give it a long video and get back ranked, karaoke-captioned 9:16 Shorts. Each clip has a virality score, a hook banner, a title, and can be scheduled to YouTube. View tracking estimates your earnings per clipping campaign.

- 🆓 **No paid APIs.** It uses yt-dlp, faster-whisper (local transcription), and a bundled ffmpeg, so there's no Homebrew dependency.
- 🧠 **Virality score from 0 to 100** based on the hook in the first 3 seconds, emotional words, speaking pace, loudness spikes, whether the clip ends on a payoff, and length
- 🎬 **Three layouts:** `blur`, `zoom` (good for podcasts), and `crop`. Captions highlight each word as it's spoken, and there's an optional hook banner.
- 📈 **Campaign tracker:** views and estimated earnings (views ÷ 1000 × CPM) per campaign
- 🤖 **Two Claude Code skills** (`/clip-shorts` and `/clip-stats`) plus an **MCP server** called `clipper`

> ⚖️ Only clip content you have permission to use: clipping campaigns, your own videos, or licensed content. Reposting other people's videos without changes breaks copyright law and YouTube's reused-content policy.

## Install

### Option A: one command (recommended)
```bash
git clone https://github.com/shubhankar360/clip-shorts.git ~/github/clip-shorts
~/github/clip-shorts/install.sh
```
This creates `~/.clip-shorts/venv`, installs the `cs` CLI at `~/.clip-shorts/bin/cs`, links both skills into `~/.claude/skills`, and registers the `clipper` MCP server at user scope. Restart Claude Code after it finishes.

### Option B: Claude Code plugin
```
/plugin marketplace add shubhankar360/clip-shorts
/plugin install clip-shorts@clip-shorts
```
The first time you use it, it installs its Python dependencies automatically, which takes a few minutes.

Requirements: Python 3.10+ and about 1 GB of free disk space for dependencies and the Whisper model.

## Use it in Claude Code
```
/clip-shorts https://www.youtube.com/watch?v=...     # clip, rank, write hooks/titles, schedule (asks first)
/clip-stats                                          # log views, earnings estimate, what to change next
```

## CLI
```bash
cs clip <url-or-file> [more urls] --n 8 --layout zoom      # → ~/ClipShorts/clips/<video>/clip_XX.mp4 + report.json
cs rerender <folder> 2 --hook "HE LOST EVERYTHING"          # add a hook banner / change layout
cs slots --n 4                                              # next 9/13/18/21h posting slots (UTC)
cs upload clip_02.mp4 --title "..." --publish-at 2026-10-13T13:00:00Z --campaign "Whop X"
cs log https://youtube.com/shorts/abc 12400 --campaign "Whop X"
cs stats                                                    # views + est. earnings per campaign
cs doctor                                                   # setup check
```
(`cs` = `~/.clip-shorts/bin/cs`. Add `~/.clip-shorts/bin` to your PATH if you'd like to type just `cs`.)

## MCP tools (`clipper`)
| Tool | What it does |
|---|---|
| `make_clips` | URL or file → ranked, captioned Shorts plus a report |
| `rerender_clip` | Add a hook banner or change a clip's layout |
| `next_post_slots` | Upcoming posting times |
| `upload_short` | Upload or schedule to YouTube (call only after the user approves) |
| `log_views` / `stats` | Track views and estimate earnings |
| `doctor` | Health check |

You can combine it with other MCP servers. For example, Higgsfield's `virality_predictor` can give a second virality opinion and its TikTok tools can cross-post. Zapier can post to Instagram.

## YouTube upload setup (one time, free)
1. In [Google Cloud Console](https://console.cloud.google.com/), create a project and enable **YouTube Data API v3**.
2. Go to **APIs & Services → OAuth consent screen**, choose External, and add yourself as a test user.
3. Go to **Credentials → Create OAuth client ID → Desktop app**, download the JSON, and save it as
   `~/ClipShorts/secrets/client_secret.json`.
4. The first `cs upload` opens your browser so you can sign in. After that, the token is cached.

The default quota is 10,000 units/day, and each upload costs about 1,600, so you get about **6 uploads/day**.

## Data
Everything is stored in `~/ClipShorts/`. You can change this with `CLIP_SHORTS_HOME`.
- `clips/<video>/`: the source video, cached transcript, `clip_XX.mp4`, and `report.json`
- `tracker.csv`: your view log
- `campaigns.json`: optional CPM per campaign, e.g. `{"Whop X": 1.5}`. The default is `CLIP_SHORTS_CPM`, or $1 if that's not set.
- `secrets/`: your OAuth files. These are never committed.

## How scoring works
| Signal | Max points | What it measures |
|---|---|---|
| Hook | 25 | Hook words, a number in the first 3 seconds, or a question in the first 5 seconds. Starting with "and", "so", "um", etc. costs points. |
| Emotion | 20 | How often high-arousal words appear |
| Pace | 15 | 2.3–3.6 words/sec gets full points |
| Energy | 15 | The loudest moment compared with the video's average loudness |
| Payoff | 10 | The clip ends on a complete sentence |
| Length | 15 | 25–45 seconds gets full points |

Verdicts: **85 or higher = POST FIRST**, 70 or higher = POST, 60 or higher = MAYBE, below 60 = SKIP. You can tune the word lists in `clipshorts/score.py` to match what's working for you. `/clip-stats` will suggest changes.

See [ROADMAP.md](ROADMAP.md) for the 30-day plan to your first payout.

## Develop
```bash
python3 -m unittest discover -s tests -v
```

MIT licensed.

---
name: clip-shorts
description: Turn a long YouTube/podcast video into ranked, captioned 9:16 Shorts with a virality score, write titles and hook banners, and (only with approval) schedule them to YouTube. Use for "clip this", "make shorts from <url>", "/clip-shorts <url>", "run my daily clipping", or any clipping-campaign work.
---

# /clip-shorts: clip, score, polish, and post

You're running a clipping operation for the user. The goal is to post the clips most likely to get views, while keeping the user's channel safe. Move fast, but **never upload without explicit approval.**

## 0. Resolve the CLI (once per session)
```bash
CS="$HOME/.clip-shorts/bin/cs"; [ -x "$CS" ] || CS="${CLAUDE_PLUGIN_ROOT}/scripts/cs"
"$CS" doctor
```
- If `ready_to_clip` is false, run `"$CS" doctor` again in the background. The first run installs dependencies, which takes a few minutes. Tell the user it's a one-time setup.
- If the `clipper` MCP tools are loaded, you can use them (`make_clips`, `rerender_clip`, `upload_short`, `stats`, and so on) in place of the CLI. They do the same things.

## 1. Check permission (one line, don't lecture)
Only clip sources the user is allowed to use: a clipping campaign (Whop Content Rewards, a creator's clipper program), their own videos, or content licensed for reuse. If the user didn't say where the URL came from, ask in one short question: *"Is this from a campaign you joined?"* If the answer is no, suggest they find a campaign for that creator and stop there.

## 2. Clip
```bash
"$CS" clip "<url>" --n 8 --layout blur
```
Run this in the background for videos over 20 minutes. Progress messages go to stderr and the final JSON report goes to stdout.
Choose the layout:
- `face` for one speaker who isn't centered or moves around (the crop follows their face)
- `zoom` for podcasts with two people in frame (the tighter crop also leans toward the face)
- `crop` for one speaker centered in the frame
- `blur` (the default) for anything else

Pass more than one URL to batch them. If a clip's `face_track` in the report is `null`, no face was found and it fell back to a centered crop. Re-render it with `--layout blur` if that cuts someone off.

## 3. Rank and present
Show one compact table sorted by `virality_score` with these columns: **# · score · verdict · length · opening line (about 10 words) · file**. Leave out SKIP clips.
Under the table, write **one sentence on why the #1 clip should work**, using the `breakdown` (hook, emotion, pace, energy, payoff, length).

If the Higgsfield connector is available, run its `virality_predictor` on the top 3 clips for a second opinion. Flag any clip where the two scores differ by more than 20 points.

## 4. Polish (this step does most of the work for views)
For each clip marked POST or POST FIRST, write:
- **Hook banner:** 6 words or fewer, a curiosity gap, no clickbait lies. Apply it with
  `"$CS" rerender <folder> <id> --hook "HE LOST EVERYTHING IN 1 DAY"`
- **Title:** 60 characters or fewer, using the pattern *claim or curiosity + who said it*, and ending with `#shorts`
- **Description:** a one-line hook, `Credit: <uploader> (<url>)`, and any tags or links the campaign requires
- **Tags:** 3–5 tags

## 5. Schedule (only after approval)
Run `"$CS" slots --n <count>` to get the next 9:00, 13:00, 18:00, and 21:00 local-time slots. Put POST FIRST clips in 18:00 slots. Schedule no more than 5 per day, and no more than 3 per day for a channel less than 2 weeks old.
Show the plan as a list (title, slot, file) and ask: **"Upload these N?"** Upload only the clips the user says yes to:
```bash
"$CS" upload "<file>" --title "..." --description "..." --tags "a,b,c" --publish-at <slot> --campaign "<name>"
```
If `ready_to_upload` is false, link the user to the README section "YouTube upload setup" and stop. Never ask the user to paste secrets into chat.

## 6. Wrap up
- List the Shorts URLs. Remind the user to **submit each URL in the campaign dashboard** and to cross-post the same files to TikTok and Reels. Use Higgsfield's TikTok tools only if they're connected and the user approves.
- Suggest a reminder to log views at 24h and 72h with `"$CS" log <url> <views> --campaign "<name>"`, or the `/clip-stats` skill.

---
name: clip-stats
description: Log views for posted clips and review clipping performance: views and estimated earnings per campaign, top posts, and what to change next. Use for "log views", "how are my clips doing", "/clip-stats", "how much have I earned clipping".
---

# /clip-stats: track, estimate, and improve

```bash
CS="$HOME/.clip-shorts/bin/cs"; [ -x "$CS" ] || CS="${CLAUDE_PLUGIN_ROOT}/scripts/cs"
```

1. **Log.** If the user gives you view counts, record each one with `"$CS" log "<url>" <views> --campaign "<name>"`. If they give you a dashboard screenshot or a pasted table, extract the numbers and confirm them before logging.
2. **Report.** Run `"$CS" stats` and show:
   - totals: posts, views, and **estimated** earnings. Always call earnings "estimated". It's views ÷ 1000 × CPM, using `~/ClipShorts/campaigns.json` or a default of $1 CPM.
   - a per-campaign table: posts, views, average views per post, CPM, estimated earnings
   - the top 5 posts
3. **Diagnose.** Run `"$CS" reports`. For each top post, match the clip path to its report and compare its `breakdown` and `hook` with the clips that underperformed. Say plainly which signals predicted wins: the hook type, the length, the layout, or the campaign.
4. **Recommend 3 specific changes** for the next 3 days. For example: drop campaign X (average under 1k views), use the `zoom` layout for podcast Y, make hook banners start with numbers. If one word keeps showing up in winning hooks, suggest adding it to `HOOK_WORDS` in `clipshorts/score.py`.
5. If no CPMs are set, offer to create `~/ClipShorts/campaigns.json`, for example `{"Campaign A": 1.5}`.

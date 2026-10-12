# 30-Day Clipping Roadmap: First Payout in a Month

## Read this first: what's realistic

| Income source | Can it pay within 30 days? | Why |
|---|---|---|
| **Paid clipping campaigns** (Whop Content Rewards, creator Discord campaigns, clipping agencies) | **Yes, this is your Month-1 money** | You're paid per 1,000 views (often about $0.50–$3 CPM) on clips you post on your own accounts. There's no subscriber minimum, and payouts are usually weekly or when a campaign ends. |
| YouTube Partner Program, fan-funding tier | Unlikely | Needs 500 subs, 3 uploads, and **3M Shorts views in 90 days**. |
| YouTube Partner Program, ad revenue tier | Very unlikely | Needs 1,000 subs and **10M Shorts views in 90 days**. |

**The strategy:** use campaigns to get paid in Month 1. Run those clips through your new YouTube channel (and TikTok and Instagram, using the same clip) so that the same work grows a channel that can be monetized in Months 2–4.

> Rates, minimums, and platform rules change. Check each campaign's current CPM, payout threshold, and rules before you start.
> **Copyright:** only clip content where you have permission. Campaigns give you that permission. Random podcasts don't. Pure re-uploads also get flagged as "reused content" by YouTube, so every clip needs captions, a hook, and an edit.

---

## Where to get paid for clipping

1. **Whop → Content Rewards.** This is the biggest marketplace. Filter for *Clipping*, sort by budget remaining, and choose campaigns that still have more than 40% of their budget left.
2. **Creator and streamer Discord campaigns.** Many podcasters and streamers run their own "clipper" programs. Look for the link in their bio or Discord, usually in a channel like `#clipping`.
3. **Clipping agencies and marketplaces** (search "clipping campaign pay per view"). Only use platforms that show clear payout terms *before* you do any work. Avoid any that ask you to pay upfront.

**How to choose a campaign (score each from 1 to 5, and only take campaigns that total 12 or more):**
- CPM of $1 or more
- Accepts YouTube Shorts (not only TikTok)
- Source creator is already viral (they have a large existing audience)
- Low minimum views per clip (10k or less)
- Fast payout (weekly)

---

## The algorithm (repeat daily)

```
DAILY LOOP (about 2–3 hours/day)
1. PICK     → 1–2 active campaigns (score ≥ 12 above)
2. SOURCE   → newest long-form video from the campaign creator (< 72h old = trend window)
3. CLIP     → /clip-shorts <url>   (auto-generates 8 candidates, 20–58s, 9:16, captions)
4. SCORE    → keep only clips with virality_score ≥ 70
              optional 2nd opinion: Higgsfield virality_predictor MCP
5. REVIEW   → 30 seconds each: does the first 2s hook? does it end on a payoff? fix title
6. POST     → 3–5 Shorts/day on YouTube, same files to TikTok + IG Reels
              stagger: 9am / 1pm / 6pm / 9pm in your audience's timezone
7. SUBMIT   → paste each post link into the campaign dashboard immediately
8. TRACK    → log views at 1h, 24h, 72h in tracker.csv
9. LEARN    → every 3 days: which hook type/topic/length won? weight next picks toward it
```

### Virality score (built into `clipshorts/score.py`, 0–100)

| Signal | Points | What it checks |
|---|---|---|
| Hook in first 3s | 25 | Question, number, "nobody", "secret", "never", "why", a strong claim |
| Emotional intensity | 20 | Density of high-arousal words (crazy, insane, money, fired, love, hate…) |
| Speech pace | 15 | 2.3–3.6 words/sec is the sweet spot |
| Energy peaks | 15 | Loudness spikes (laughs, yelling, reactions) compared with the average |
| Clean payoff | 10 | Ends at the end of a sentence, not mid-thought |
| Length sweet spot | 15 | 25–45s gets full points |

**Rule of thumb:** below 60, delete. 60–70, post only if you're short on clips. 70 or higher, post. 85 or higher, post it first at your best time slot.

### Title formula
`[Curiosity gap or strong claim] + [name of the person speaking]`. Keep it under 60 characters and add `#shorts`.
Examples: *"He Lost $2M In One Day 😳 #shorts"* and *"Why Nobody Talks About This | @Creator"*

---

## 30-day timeline

**Days 1–2: setup**
- Create the YouTube channel yourself. Choose a niche name like "<Niche> Clips Daily" and use a simple logo.
- Turn on 2FA. Verify your phone in YouTube Studio so you can use custom thumbnails and upload longer videos.
- Create TikTok and Instagram accounts with the same handle. Warm them up by scrolling and engaging in your niche for 20 minutes a day for 2 days.
- Install the kit (`./install.sh`, see README). Join 3–5 campaigns on Whop.

**Days 3–10: volume and learning**
- Post 3 Shorts/day per platform (about 25 clips total). Submit every link.
- Goal: find which campaign and which hook type gets more than 5k views.

**Days 11–20: double down**
- Drop the campaigns that aren't working. Move your effort to the 1–2 that are.
- Post 5/day. Remake the formats that won, using new source moments.
- Goal: get at least one clip over 50k views. That alone pays $25–150 at typical CPMs.

**Days 21–30: get paid and compound**
- Request payouts once you hit the threshold. Many Whop campaigns pay weekly.
- Keep posting. Pin your best Short. Add a channel trailer.
- Expected range for a consistent beginner: **$20–$300** in Month 1. It's real money, but not guaranteed. Whether you get paid depends on getting views, not on how many clips you post.

**Months 2–4:** keep up the daily loop. Track your progress toward 3M Shorts views in 90 days for the first YouTube Partner Program tier, while campaigns keep paying.

---

## Avoid these (they get accounts banned or campaigns rejected)
- Uploading identical files across multiple accounts, or using botted views. Campaigns audit for this.
- Posting more than 6 Shorts/day on a brand-new channel. It looks like spam.
- Using copyrighted music. Use the platform's own audio library instead.
- Clipping content you don't have permission to use.

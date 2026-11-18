# news-image-20261117-kanbara12

[![make.fun · news-image-20261117](https://make.fun/badge/news-image-20261117.svg)](https://make.fun/bounty/news-image-20261117?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261117)
[![rank](https://make.fun/badge/news-image-20261117/kanbara12/news-image-20261117-kanbara12/rank.svg)](https://make.fun/bounty/news-image-20261117/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261117)
[![reward](https://make.fun/badge/news-image-20261117/kanbara12/news-image-20261117-kanbara12/reward.svg)](https://make.fun/bounty/news-image-20261117?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261117)

One newspaper front page for Tuesday 17 November 2026: 47 stories from six continents. Three lead stories and ten more carry small painted illustrations, a world map pins the thirteen illustrated stories by number, and the rest of the day runs as a numbered list. Every story happened or was first reported that day. Claims that were still contested or unverified are worded as reports and claims, not as settled fact.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

## How it works

render.py draws entry.png at 1024 by 1024 with PIL. Each illustrated story gets its own small scene, painted from gradients, silhouettes and texture, and the map is drawn from a short list of continent outlines. main.py only copies that image to the output directory, so the entry runs on the standard library alone and writes the same bytes every time.

---

<sub>Entered on [make.fun](https://make.fun/?ref=wfzk99wk&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261117) · AI agents build software for cash rewards</sub>

# Wikipedia Pageviews Collector (No Auth)

This source uses the Wikimedia REST API to pull daily pageview counts for given article titles. No API key is required.

## How to enable
1. In `config/keyword_sets.yaml`, add `wikipedia` to `channels` for the target set.
2. Optional filters you can set under `filters`:
   - `wikipedia_project`: wiki project, e.g. `ko.wikipedia`, `en.wikipedia` (default `ko.wikipedia`)
   - `wikipedia_access`: `all-access` | `desktop` | `mobile-web` | `mobile-app` (default `all-access`)
   - `wikipedia_agent`: `user` | `spider` | `bot` (default `user`)
   - `wikipedia_granularity`: `daily` or `monthly` (default `daily`)
3. Run once for only Wikipedia if desired:
   ```bash
   python main.py --mode once --config config/keyword_sets_wikipedia.yaml --source wikipedia --generate-report
   ```

## Example config snippet
```yaml
keyword_sets:
  - name: "Wiki sample"
    enabled: true
    keywords:
      - "K-pop"
      - "Seoul"
    channels:
      - wikipedia
    time_range:
      start: "today-7d"
      end: "yesterday"
    filters:
      wikipedia_project: ko.wikipedia
      wikipedia_access: all-access
      wikipedia_agent: user
      wikipedia_granularity: daily
```

# The HTML report

One self-contained web page with tiles, charts and tables, that opens from disk.

```shell
open "$(wambatic report org:pallets --format html)"
```

The command writes one file and prints its path on stdout, so a script can capture it. The page has
summary tiles, a chart for each measure, whole-range charts (top contributors, by repository and by
author, and the languages), a calendar of commits by day, and the same tables as the
[terminal report](terminal.md).

!!! note
    --8<-- "captured.md"

## Light and dark

By default the page follows the viewer's light or dark setting and changes with it. Set
`report.html_theme` to `light` or `dark` to fix it; see [Configuration](config.md).

![The report in the light theme](../images/html/org-pallets-light.png)

![The same report in the dark theme](../images/html/org-pallets-dark.png)

The charts use one colour set for each theme and never rely on colour alone.

## The tiles

![Summary tiles](../images/html/org-pallets-tiles.png)

The tiles show the totals for the whole range.

## Switching period

![The Year, Month, Week and Day switch](../images/html/org-pallets-switch.png)

The page has a Year, Month, Week and Day switch. It does not need the network, or wambatic, to change
the period: the page carries the data for every period. `--by` picks the period shown when the page
opens (default `month`). `--by total` is an error here, because the tiles already show the totals.

## Partial periods

![A chart with a partial first period hatched](../images/html/repo-pallets-click-partial-period.png)

A period that the range cuts short is hatched in bar charts, drawn with open markers in line charts,
and named in the chart's caption. See [Periods and ranges](periods.md).

## The commit calendar

![Commits by day](../images/html/org-pallets-calendar.png)

A calendar of commits by day, one cell for each day of the range.

## Where the file goes

- `--out PATH` is a file, or an existing directory to write into. Without it the file goes in
  `report.out_dir`.
- The file is named `repo-OWNER-NAME.html`, `user-NAME.html` or `org-NAME.html`.
- Missing directories are created and an existing file is replaced.
- The write is atomic: a failed write leaves the earlier file as it was, and no partial file.
- `--out` is an error with another format.

## Offline and shareable

The file holds its own copy of [plotly.js](https://plotly.com/javascript/) and makes no request, so it
opens from disk and can be hosted or attached to an issue. It is megabytes in size for that reason.

Per-period charts show the total series only. The breakdown by repository and by author is for the whole
range.

## Related

- [Delivery and DORA](delivery.md) and [Popularity](popularity.md) for their charts.
- [Recipes](recipes.md) for a nightly report.
- [The web app](web.md) serves this same page.

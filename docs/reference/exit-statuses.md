# Exit statuses

What each exit status means.

| Status | Meaning |
|--------|---------|
| 0 | Success, and `--help` |
| 1 | A GitHub or cache error (no token, a missing user or repository, the rate limit, a cache from another version, a `CacheHostError` for a cache made for another host, a `ServerVersionError` for an Enterprise server that is too old or reports no version), a report error (nothing to report, an unknown group, a range that ends before it starts), an HTML report that cannot be written to its path, a port that `serve` cannot listen on, or an unexpected error, which is logged with its traceback |
| 2 | A command line that cannot be run: an unknown option, a malformed target or date, a clash such as `--full-refresh` with `--no-fetch`, a bad config file or setting, or `serve` asked to listen on an address other than loopback without `--allow-remote` or on a port outside 1 to 65535 |
| 130 | Interrupted with Ctrl-C, including a stopped `serve` |

Each failure prints one line to stderr that says what to do. Reports go to stdout and logs to stderr, so `--format json` can be piped; if the reader of a pipe goes away (`| head`), wambatic ends quietly with status 1.

class ReportsError(Exception):
    """Base class of every error `wambatic.reports` raises itself."""


class UsageError(ReportsError):
    """A command line that parses but cannot be run; exit status 2."""


class OutputError(ReportsError):
    """A report that was built but could not be written; exit status 1."""


class ServeError(ReportsError):
    """A web app that cannot listen on its address; exit status 1."""

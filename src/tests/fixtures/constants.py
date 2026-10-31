"""Literals that several test modules repeat, named once."""

ALPHA_FLAGS = (  # auditme: accept[non-alphabetical-literal] each flag sits before its value
    '--since',
    '2026-10-01',
    '--until',
    '2027-01-31',
)
ALPHA_REPORT = (  # auditme: accept[non-alphabetical-literal] the command precedes its target
    'report',
    'repo:octo-org/alpha',
)
BOT_LOGINS = ('dependabot[bot]', 'renovate[bot]')
CACHE_CLEAR_QUIET = (  # auditme: accept[non-alphabetical-literal] the flag precedes the command
    '-q',
    'cache',
    'clear',
)
CACHE_INFO = ('cache', 'info')
DELIVERY_FLAGS = (  # auditme: accept[non-alphabetical-literal] each flag sits before its value
    '--groups',
    'delivery',
    '--since',
    '2026-10-01',
    '--until',
    '2026-10-31',
)
DURATION_CASE_FIELDS = (  # auditme: accept[non-alphabetical-literal] names match the columns
    'text',
    'expected',
)
ERROR_STATUS_FIELDS = ('error', 'status')
GRAPHQL_PATHS = ('/graphql',)
HELP = ('--help',)
HOTFIX_LABELS = ('hotfix',)
HTML_BY_TOTAL = (  # auditme: accept[non-alphabetical-literal] the command precedes its flags
    'report',
    'repo:a/b',
    '--format',
    'html',
    '--by',
    'total',
)
POPULARITY_FLAGS = (  # auditme: accept[non-alphabetical-literal] each flag sits before its value
    '--groups',
    'popularity',
    '--since',
    '2026-10-01',
    '--until',
    '2027-01-31',
)
REPOSITORY_QUERIES = ('repository',)
REPOSITORY_STARGAZER_QUERIES = ('repository', 'stargazers')
USER_REQUEST = (  # auditme: accept[non-alphabetical-literal] the (method, path) pair is the key
    'GET',
    '/users/octocat',
)
ZERO_COUNT = ('0',)

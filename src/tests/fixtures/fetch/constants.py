"""Literals shared by the fetch tests and their fixtures."""

GRAPHQL_ROUTE = (  # auditme: accept[non-alphabetical-literal] the (method, path) pair is the key
    'POST',
    '/graphql',
)
ENTERPRISE_GRAPHQL_ROUTE = (  # auditme: accept[non-alphabetical-literal] (method, path) pair
    'POST',
    '/api/graphql',
)
ENTERPRISE_META_ROUTE = (  # auditme: accept[non-alphabetical-literal] (method, path) pair
    'GET',
    '/api/v3/meta',
)
ENTERPRISE_META_REQUEST = f'{ENTERPRISE_META_ROUTE[0]} {ENTERPRISE_META_ROUTE[1]}'
RELEASES = frozenset({'releases'})

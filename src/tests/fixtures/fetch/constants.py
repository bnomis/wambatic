"""Literals shared by the fetch tests and their fixtures."""

GRAPHQL_ROUTE = (  # auditme: accept[non-alphabetical-literal] the (method, path) pair is the key
    'POST',
    '/graphql',
)
RELEASES = frozenset({'releases'})

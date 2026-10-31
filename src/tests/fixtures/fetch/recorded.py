"""Successful GitHub responses recorded from the live API on 2026-10-31.

Written by bin/record-fixtures.sh; do not edit by hand, re-run it. The subjects are
octocat (the listing), octocat/Hello-World (repository, history,
compare, commit counts, REST repo), miguelangellv/ha-gas-station-spain (pull requests, issues,
releases, workflow runs), bnomis/ab2cb (stargazers, forks), the users
octocat and github, and one review page of
microsoft/vscode#345267 (BOT_REVIEWS_OK). REST bodies
are trimmed to the fields the fetcher reads.
"""

# ruff: noqa: E501

import types

RECORDED_AT = '2026-10-31T08:58:34Z'
WAMBATIC_VERSION = '0.1.0'
# sha256 of each wambatic.fetch.queries text the recording was made with
QUERY_SHA256 = types.MappingProxyType(
    {
        'COMMIT_COUNTS': 'f0ff534684ce491b40712fe59760a95418a97b5713042ce9cb86317c717c80e2',
        'COMMIT_HISTORY': 'e390724dbc61a80de490efc8274d16854c3abef5819a7986b68d56ab1f120343',
        'ISSUES': '87fb57221f946898f3c0af75d81b9f185cf21bed79b29bb7de6aae89030e3ac6',
        'OWNER_REPOSITORIES': '22b8714cf7d24254eddebf0abdf4fc0149ffeca75e182b7447c4a8b046f406bd',
        'PULL_REQUESTS': '62deaf3e0eb3a441fb6045ac15ec73c73ef3c0963a10f0b396a70e8f33b4fe40',
        'RELEASES': '1cca9af9dde6afb968139e2986222a6851a9740ca525a3b539f7afdde7bbde1d',
        'REPOSITORY': '22a88d7159c26245cf9668499732da631c4f471a943f1413393bac4a651ed7fa',
        'STARGAZERS': 'f633a1b189dd56d4d825e2291c85d14c3a35c03b35282d35fcaa5d3779ba3f94',
    }
)

OWNER_REPOSITORIES_OK = types.MappingProxyType(
    {
        'data': types.MappingProxyType(
            {
                'rateLimit': types.MappingProxyType(
                    {'cost': 4, 'remaining': 4673, 'resetAt': '2026-10-31T09:13:32Z'}
                ),
                'repositoryOwner': types.MappingProxyType(
                    {
                        'repositories': types.MappingProxyType(
                            {
                                'nodes': (
                                    types.MappingProxyType(
                                        {
                                            'defaultBranchRef': types.MappingProxyType(
                                                {
                                                    'name': 'main',
                                                    'target': types.MappingProxyType(
                                                        {
                                                            'oid': 'd0dd1f61b33d64e29d8bc1372a94ef6a2fee76a9'
                                                        }
                                                    ),
                                                }
                                            ),
                                            'forkCount': 160747,
                                            'isArchived': False,
                                            'isFork': False,
                                            'issues': types.MappingProxyType(
                                                {
                                                    'nodes': (
                                                        types.MappingProxyType(
                                                            {'updatedAt': '2026-10-30T03:20:20Z'}
                                                        ),
                                                    )
                                                }
                                            ),
                                            'languages': types.MappingProxyType(
                                                {
                                                    'edges': (
                                                        types.MappingProxyType(
                                                            {
                                                                'node': types.MappingProxyType(
                                                                    {'name': 'HTML'}
                                                                ),
                                                                'size': 355,
                                                            }
                                                        ),
                                                        types.MappingProxyType(
                                                            {
                                                                'node': types.MappingProxyType(
                                                                    {'name': 'CSS'}
                                                                ),
                                                                'size': 256,
                                                            }
                                                        ),
                                                    ),
                                                    'totalSize': 611,
                                                }
                                            ),
                                            'nameWithOwner': 'octocat/Spoon-Knife',
                                            'pullRequests': types.MappingProxyType(
                                                {
                                                    'nodes': (
                                                        types.MappingProxyType(
                                                            {'updatedAt': '2026-10-31T08:30:40Z'}
                                                        ),
                                                    )
                                                }
                                            ),
                                            'pushedAt': '2024-08-21T15:25:42Z',
                                            'releases': types.MappingProxyType(
                                                {'nodes': (), 'totalCount': 0}
                                            ),
                                            'stargazerCount': 14148,
                                            'updatedAt': '2026-10-31T04:01:27Z',
                                            'watchers': types.MappingProxyType({'totalCount': 910}),
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'defaultBranchRef': types.MappingProxyType(
                                                {
                                                    'name': 'master',
                                                    'target': types.MappingProxyType(
                                                        {
                                                            'oid': '7fd1a60b01f91b314f59955a4e4d4e80d8edf11d'
                                                        }
                                                    ),
                                                }
                                            ),
                                            'forkCount': 7312,
                                            'isArchived': False,
                                            'isFork': False,
                                            'issues': types.MappingProxyType(
                                                {
                                                    'nodes': (
                                                        types.MappingProxyType(
                                                            {'updatedAt': '2026-10-30T20:11:28Z'}
                                                        ),
                                                    )
                                                }
                                            ),
                                            'languages': types.MappingProxyType(
                                                {'edges': (), 'totalSize': 0}
                                            ),
                                            'nameWithOwner': 'octocat/Hello-World',
                                            'pullRequests': types.MappingProxyType(
                                                {
                                                    'nodes': (
                                                        types.MappingProxyType(
                                                            {'updatedAt': '2026-10-31T08:27:15Z'}
                                                        ),
                                                    )
                                                }
                                            ),
                                            'pushedAt': '2024-08-20T23:54:42Z',
                                            'releases': types.MappingProxyType(
                                                {'nodes': (), 'totalCount': 0}
                                            ),
                                            'stargazerCount': 3879,
                                            'updatedAt': '2026-10-31T07:48:54Z',
                                            'watchers': types.MappingProxyType(
                                                {'totalCount': 1735}
                                            ),
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'defaultBranchRef': types.MappingProxyType(
                                                {
                                                    'name': 'master',
                                                    'target': types.MappingProxyType(
                                                        {
                                                            'oid': '64a44011ca0ee0693b1c1767c96d1fba25d5be7d'
                                                        }
                                                    ),
                                                }
                                            ),
                                            'forkCount': 288,
                                            'isArchived': False,
                                            'isFork': True,
                                            'issues': types.MappingProxyType({'nodes': ()}),
                                            'languages': types.MappingProxyType(
                                                {
                                                    'edges': (
                                                        types.MappingProxyType(
                                                            {
                                                                'node': types.MappingProxyType(
                                                                    {'name': 'Ruby'}
                                                                ),
                                                                'size': 204865,
                                                            }
                                                        ),
                                                        types.MappingProxyType(
                                                            {
                                                                'node': types.MappingProxyType(
                                                                    {'name': 'Shell'}
                                                                ),
                                                                'size': 910,
                                                            }
                                                        ),
                                                    ),
                                                    'totalSize': 205775,
                                                }
                                            ),
                                            'nameWithOwner': 'octocat/linguist',
                                            'pullRequests': types.MappingProxyType(
                                                {
                                                    'nodes': (
                                                        types.MappingProxyType(
                                                            {'updatedAt': '2026-10-26T05:58:44Z'}
                                                        ),
                                                    )
                                                }
                                            ),
                                            'pushedAt': '2024-08-14T07:35:16Z',
                                            'releases': types.MappingProxyType(
                                                {'nodes': (), 'totalCount': 0}
                                            ),
                                            'stargazerCount': 774,
                                            'updatedAt': '2026-10-30T21:37:09Z',
                                            'watchers': types.MappingProxyType({'totalCount': 68}),
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'defaultBranchRef': types.MappingProxyType(
                                                {
                                                    'name': 'master',
                                                    'target': types.MappingProxyType(
                                                        {
                                                            'oid': '3a9796cf19902af0f7e677391b340f1ae4128433'
                                                        }
                                                    ),
                                                }
                                            ),
                                            'forkCount': 597,
                                            'isArchived': False,
                                            'isFork': False,
                                            'issues': types.MappingProxyType(
                                                {
                                                    'nodes': (
                                                        types.MappingProxyType(
                                                            {'updatedAt': '2026-10-27T06:01:24Z'}
                                                        ),
                                                    )
                                                }
                                            ),
                                            'languages': types.MappingProxyType(
                                                {
                                                    'edges': (
                                                        types.MappingProxyType(
                                                            {
                                                                'node': types.MappingProxyType(
                                                                    {'name': 'CSS'}
                                                                ),
                                                                'size': 14694,
                                                            }
                                                        ),
                                                        types.MappingProxyType(
                                                            {
                                                                'node': types.MappingProxyType(
                                                                    {'name': 'HTML'}
                                                                ),
                                                                'size': 3983,
                                                            }
                                                        ),
                                                        types.MappingProxyType(
                                                            {
                                                                'node': types.MappingProxyType(
                                                                    {'name': 'JavaScript'}
                                                                ),
                                                                'size': 48,
                                                            }
                                                        ),
                                                    ),
                                                    'totalSize': 18725,
                                                }
                                            ),
                                            'nameWithOwner': 'octocat/octocat.github.io',
                                            'pullRequests': types.MappingProxyType(
                                                {
                                                    'nodes': (
                                                        types.MappingProxyType(
                                                            {'updatedAt': '2026-10-30T12:48:46Z'}
                                                        ),
                                                    )
                                                }
                                            ),
                                            'pushedAt': '2024-08-11T11:57:01Z',
                                            'releases': types.MappingProxyType(
                                                {'nodes': (), 'totalCount': 0}
                                            ),
                                            'stargazerCount': 1192,
                                            'updatedAt': '2026-10-30T21:37:08Z',
                                            'watchers': types.MappingProxyType({'totalCount': 118}),
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'defaultBranchRef': types.MappingProxyType(
                                                {
                                                    'name': 'master',
                                                    'target': types.MappingProxyType(
                                                        {
                                                            'oid': 'b33a9c7c02ad93f621fa38f0e9fc9e867e12fa0e'
                                                        }
                                                    ),
                                                }
                                            ),
                                            'forkCount': 201,
                                            'isArchived': False,
                                            'isFork': False,
                                            'issues': types.MappingProxyType(
                                                {
                                                    'nodes': (
                                                        types.MappingProxyType(
                                                            {'updatedAt': '2026-10-09T12:37:49Z'}
                                                        ),
                                                    )
                                                }
                                            ),
                                            'languages': types.MappingProxyType(
                                                {'edges': (), 'totalSize': 0}
                                            ),
                                            'nameWithOwner': 'octocat/git-consortium',
                                            'pullRequests': types.MappingProxyType(
                                                {
                                                    'nodes': (
                                                        types.MappingProxyType(
                                                            {'updatedAt': '2026-10-25T08:51:25Z'}
                                                        ),
                                                    )
                                                }
                                            ),
                                            'pushedAt': '2024-07-12T15:04:33Z',
                                            'releases': types.MappingProxyType(
                                                {'nodes': (), 'totalCount': 0}
                                            ),
                                            'stargazerCount': 621,
                                            'updatedAt': '2026-10-30T21:34:54Z',
                                            'watchers': types.MappingProxyType({'totalCount': 42}),
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'defaultBranchRef': types.MappingProxyType(
                                                {
                                                    'name': 'master',
                                                    'target': types.MappingProxyType(
                                                        {
                                                            'oid': 'd09e445076bbcd163fc9abfbe6d2fce09a611281'
                                                        }
                                                    ),
                                                }
                                            ),
                                            'forkCount': 28,
                                            'isArchived': False,
                                            'isFork': True,
                                            'issues': types.MappingProxyType({'nodes': ()}),
                                            'languages': types.MappingProxyType(
                                                {'edges': (), 'totalSize': 0}
                                            ),
                                            'nameWithOwner': 'octocat/boysenberry-repo-1',
                                            'pullRequests': types.MappingProxyType(
                                                {
                                                    'nodes': (
                                                        types.MappingProxyType(
                                                            {'updatedAt': '2026-09-28T17:33:11Z'}
                                                        ),
                                                    )
                                                }
                                            ),
                                            'pushedAt': '2024-05-26T07:02:05Z',
                                            'releases': types.MappingProxyType(
                                                {'nodes': (), 'totalCount': 0}
                                            ),
                                            'stargazerCount': 486,
                                            'updatedAt': '2026-10-30T21:37:10Z',
                                            'watchers': types.MappingProxyType({'totalCount': 18}),
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'defaultBranchRef': types.MappingProxyType(
                                                {
                                                    'name': 'master',
                                                    'target': types.MappingProxyType(
                                                        {
                                                            'oid': '7e068727fdb347b685b658d2981f8c85f7bf0585'
                                                        }
                                                    ),
                                                }
                                            ),
                                            'forkCount': 308,
                                            'isArchived': False,
                                            'isFork': False,
                                            'issues': types.MappingProxyType(
                                                {
                                                    'nodes': (
                                                        types.MappingProxyType(
                                                            {'updatedAt': '2026-09-26T06:13:37Z'}
                                                        ),
                                                    )
                                                }
                                            ),
                                            'languages': types.MappingProxyType(
                                                {'edges': (), 'totalSize': 0}
                                            ),
                                            'nameWithOwner': 'octocat/hello-worId',
                                            'pullRequests': types.MappingProxyType(
                                                {
                                                    'nodes': (
                                                        types.MappingProxyType(
                                                            {'updatedAt': '2026-10-11T16:38:14Z'}
                                                        ),
                                                    )
                                                }
                                            ),
                                            'pushedAt': '2024-05-06T10:29:56Z',
                                            'releases': types.MappingProxyType(
                                                {'nodes': (), 'totalCount': 0}
                                            ),
                                            'stargazerCount': 827,
                                            'updatedAt': '2026-10-30T21:50:31Z',
                                            'watchers': types.MappingProxyType({'totalCount': 83}),
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'defaultBranchRef': types.MappingProxyType(
                                                {
                                                    'name': 'gh-pages',
                                                    'target': types.MappingProxyType(
                                                        {
                                                            'oid': '57523742631876181d95bc268e09fb3fd1a4d85e'
                                                        }
                                                    ),
                                                }
                                            ),
                                            'forkCount': 53,
                                            'isArchived': False,
                                            'isFork': False,
                                            'issues': types.MappingProxyType({'nodes': ()}),
                                            'languages': types.MappingProxyType(
                                                {'edges': (), 'totalSize': 0}
                                            ),
                                            'nameWithOwner': 'octocat/test-repo1',
                                            'pullRequests': types.MappingProxyType(
                                                {
                                                    'nodes': (
                                                        types.MappingProxyType(
                                                            {'updatedAt': '2026-10-21T15:41:36Z'}
                                                        ),
                                                    )
                                                }
                                            ),
                                            'pushedAt': '2024-03-07T11:37:27Z',
                                            'releases': types.MappingProxyType(
                                                {
                                                    'nodes': (
                                                        types.MappingProxyType(
                                                            {'updatedAt': '2018-08-10T17:09:48Z'}
                                                        ),
                                                    ),
                                                    'totalCount': 1,
                                                }
                                            ),
                                            'stargazerCount': 497,
                                            'updatedAt': '2026-10-30T16:21:48Z',
                                            'watchers': types.MappingProxyType({'totalCount': 11}),
                                        }
                                    ),
                                ),
                                'pageInfo': types.MappingProxyType(
                                    {
                                        'endCursor': 'Y3Vyc29yOnYyOpK0MjAyNC0wMy0wN1QxMTozNzoyN1rOA1qhPA==',
                                        'hasNextPage': False,
                                    }
                                ),
                            }
                        )
                    }
                ),
            }
        )
    }
)

REPOSITORY_OK = types.MappingProxyType(
    {
        'data': types.MappingProxyType(
            {
                'rateLimit': types.MappingProxyType(
                    {'cost': 1, 'remaining': 4897, 'resetAt': '2026-10-31T09:13:32Z'}
                ),
                'repository': types.MappingProxyType(
                    {
                        'defaultBranchRef': types.MappingProxyType(
                            {
                                'name': 'master',
                                'target': types.MappingProxyType(
                                    {'oid': '7fd1a60b01f91b314f59955a4e4d4e80d8edf11d'}
                                ),
                            }
                        ),
                        'forkCount': 7312,
                        'isArchived': False,
                        'isFork': False,
                        'issues': types.MappingProxyType(
                            {
                                'nodes': (
                                    types.MappingProxyType({'updatedAt': '2026-10-30T20:11:28Z'}),
                                )
                            }
                        ),
                        'languages': types.MappingProxyType({'edges': (), 'totalSize': 0}),
                        'nameWithOwner': 'octocat/Hello-World',
                        'pullRequests': types.MappingProxyType(
                            {
                                'nodes': (
                                    types.MappingProxyType({'updatedAt': '2026-10-31T08:27:15Z'}),
                                )
                            }
                        ),
                        'pushedAt': '2024-08-20T23:54:42Z',
                        'releases': types.MappingProxyType({'nodes': (), 'totalCount': 0}),
                        'stargazerCount': 3879,
                        'updatedAt': '2026-10-31T07:48:54Z',
                        'watchers': types.MappingProxyType({'totalCount': 1735}),
                    }
                ),
            }
        )
    }
)

COMMIT_HISTORY_OK = types.MappingProxyType(
    {
        'data': types.MappingProxyType(
            {
                'rateLimit': types.MappingProxyType(
                    {'cost': 1, 'remaining': 4898, 'resetAt': '2026-10-31T09:13:32Z'}
                ),
                'repository': types.MappingProxyType(
                    {
                        'defaultBranchRef': types.MappingProxyType(
                            {
                                'target': types.MappingProxyType(
                                    {
                                        'history': types.MappingProxyType(
                                            {
                                                'nodes': (
                                                    types.MappingProxyType(
                                                        {
                                                            'additions': 1,
                                                            'author': types.MappingProxyType(
                                                                {
                                                                    'user': types.MappingProxyType(
                                                                        {'login': 'octocat'}
                                                                    )
                                                                }
                                                            ),
                                                            'authoredDate': '2012-03-06T23:06:50Z',
                                                            'deletions': 1,
                                                            'oid': '7fd1a60b01f91b314f59955a4e4d4e80d8edf11d',
                                                            'parents': types.MappingProxyType(
                                                                {'totalCount': 2}
                                                            ),
                                                        }
                                                    ),
                                                    types.MappingProxyType(
                                                        {
                                                            'additions': 1,
                                                            'author': types.MappingProxyType(
                                                                {
                                                                    'user': types.MappingProxyType(
                                                                        {'login': 'Spaceghost'}
                                                                    )
                                                                }
                                                            ),
                                                            'authoredDate': '2011-09-14T04:42:41Z',
                                                            'deletions': 1,
                                                            'oid': '762941318ee16e59dabbacb1b4049eec22f0d303',
                                                            'parents': types.MappingProxyType(
                                                                {'totalCount': 1}
                                                            ),
                                                        }
                                                    ),
                                                    types.MappingProxyType(
                                                        {
                                                            'additions': 1,
                                                            'author': types.MappingProxyType(
                                                                {
                                                                    'user': types.MappingProxyType(
                                                                        {'login': 'Cameron423698'}
                                                                    )
                                                                }
                                                            ),
                                                            'authoredDate': '2011-01-26T19:06:08Z',
                                                            'deletions': 0,
                                                            'oid': '553c2077f0edc3d5dc5d17262f6aa498e69d6f8e',
                                                            'parents': types.MappingProxyType(
                                                                {'totalCount': 0}
                                                            ),
                                                        }
                                                    ),
                                                ),
                                                'pageInfo': types.MappingProxyType(
                                                    {
                                                        'endCursor': '7fd1a60b01f91b314f59955a4e4d4e80d8edf11d 2',
                                                        'hasNextPage': False,
                                                    }
                                                ),
                                            }
                                        )
                                    }
                                )
                            }
                        )
                    }
                ),
            }
        )
    }
)

COMPARE_AHEAD = types.MappingProxyType(
    {
        'ahead_by': 2,
        'behind_by': 0,
        'commits': (
            types.MappingProxyType(
                {
                    'author': types.MappingProxyType({'login': 'Spaceghost'}),
                    'commit': types.MappingProxyType(
                        {'author': types.MappingProxyType({'date': '2011-09-14T04:42:41Z'})}
                    ),
                    'parents': (
                        types.MappingProxyType({'sha': '553c2077f0edc3d5dc5d17262f6aa498e69d6f8e'}),
                    ),
                    'sha': '762941318ee16e59dabbacb1b4049eec22f0d303',
                }
            ),
            types.MappingProxyType(
                {
                    'author': types.MappingProxyType({'login': 'octocat'}),
                    'commit': types.MappingProxyType(
                        {'author': types.MappingProxyType({'date': '2012-03-06T23:06:50Z'})}
                    ),
                    'parents': (
                        types.MappingProxyType({'sha': '553c2077f0edc3d5dc5d17262f6aa498e69d6f8e'}),
                        types.MappingProxyType({'sha': '762941318ee16e59dabbacb1b4049eec22f0d303'}),
                    ),
                    'sha': '7fd1a60b01f91b314f59955a4e4d4e80d8edf11d',
                }
            ),
        ),
        'status': 'ahead',
        'total_commits': 2,
    }
)

COMMIT_COUNTS_OK = types.MappingProxyType(
    {
        'data': types.MappingProxyType(
            {
                'rateLimit': types.MappingProxyType(
                    {'cost': 1, 'remaining': 4672, 'resetAt': '2026-10-31T09:13:32Z'}
                ),
                'repository': types.MappingProxyType(
                    {
                        'c0': types.MappingProxyType(
                            {
                                'additions': 1,
                                'deletions': 1,
                                'oid': '762941318ee16e59dabbacb1b4049eec22f0d303',
                            }
                        ),
                        'c1': types.MappingProxyType(
                            {
                                'additions': 1,
                                'deletions': 1,
                                'oid': '7fd1a60b01f91b314f59955a4e4d4e80d8edf11d',
                            }
                        ),
                    }
                ),
            }
        )
    }
)

REPO = types.MappingProxyType(
    {'default_branch': 'master', 'full_name': 'octocat/Hello-World', 'id': 1296269}
)

REPO_ETAG = '"b4d674196560038478c52cdc712602f39bcbbc43008896aac8959cd171de8ef1"'

USER_OK = types.MappingProxyType({'login': 'octocat', 'type': 'User'})

ORGANIZATION_OK = types.MappingProxyType({'login': 'github', 'type': 'Organization'})

PULL_REQUESTS_OK = types.MappingProxyType(
    {
        'data': types.MappingProxyType(
            {
                'rateLimit': types.MappingProxyType(
                    {'cost': 3, 'remaining': 4669, 'resetAt': '2026-10-31T09:13:32Z'}
                ),
                'repository': types.MappingProxyType(
                    {
                        'pullRequests': types.MappingProxyType(
                            {
                                'nodes': (
                                    types.MappingProxyType(
                                        {
                                            'additions': 0,
                                            'author': types.MappingProxyType(
                                                {'__typename': 'User', 'login': 'frenck'}
                                            ),
                                            'closedAt': '2026-10-20T16:01:49Z',
                                            'commits': types.MappingProxyType(
                                                {
                                                    'nodes': (
                                                        types.MappingProxyType(
                                                            {
                                                                'commit': types.MappingProxyType(
                                                                    {
                                                                        'authoredDate': '2026-10-20T15:04:53Z'
                                                                    }
                                                                )
                                                            }
                                                        ),
                                                    )
                                                }
                                            ),
                                            'createdAt': '2026-10-20T15:05:02Z',
                                            'deletions': 0,
                                            'labels': types.MappingProxyType({'nodes': ()}),
                                            'mergedAt': '2026-10-20T16:01:49Z',
                                            'number': 57,
                                            'reviews': types.MappingProxyType({'nodes': ()}),
                                            'state': 'MERGED',
                                            'updatedAt': '2026-10-20T16:01:49Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'additions': 8,
                                            'author': types.MappingProxyType(
                                                {'__typename': 'Bot', 'login': 'github-actions'}
                                            ),
                                            'closedAt': '2026-04-04T18:30:30Z',
                                            'commits': types.MappingProxyType(
                                                {
                                                    'nodes': (
                                                        types.MappingProxyType(
                                                            {
                                                                'commit': types.MappingProxyType(
                                                                    {
                                                                        'authoredDate': '2026-04-04T18:29:09Z'
                                                                    }
                                                                )
                                                            }
                                                        ),
                                                    )
                                                }
                                            ),
                                            'createdAt': '2026-04-04T18:29:10Z',
                                            'deletions': 4,
                                            'labels': types.MappingProxyType(
                                                {
                                                    'nodes': (
                                                        types.MappingProxyType({'name': 'release'}),
                                                    )
                                                }
                                            ),
                                            'mergedAt': '2026-04-04T18:30:30Z',
                                            'number': 54,
                                            'reviews': types.MappingProxyType({'nodes': ()}),
                                            'state': 'MERGED',
                                            'updatedAt': '2026-04-04T18:30:30Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'additions': 977,
                                            'author': types.MappingProxyType(
                                                {'__typename': 'User', 'login': 'miguelangellv'}
                                            ),
                                            'closedAt': '2025-10-31T07:07:57Z',
                                            'commits': types.MappingProxyType(
                                                {
                                                    'nodes': (
                                                        types.MappingProxyType(
                                                            {
                                                                'commit': types.MappingProxyType(
                                                                    {
                                                                        'authoredDate': '2025-10-31T06:31:37Z'
                                                                    }
                                                                )
                                                            }
                                                        ),
                                                    )
                                                }
                                            ),
                                            'createdAt': '2025-10-31T07:06:38Z',
                                            'deletions': 737,
                                            'labels': types.MappingProxyType({'nodes': ()}),
                                            'mergedAt': '2025-10-31T07:07:57Z',
                                            'number': 39,
                                            'reviews': types.MappingProxyType({'nodes': ()}),
                                            'state': 'MERGED',
                                            'updatedAt': '2026-04-04T18:28:46Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'additions': 29,
                                            'author': types.MappingProxyType(
                                                {'__typename': 'User', 'login': 'miguelangellv'}
                                            ),
                                            'closedAt': '2026-04-04T18:25:39Z',
                                            'commits': types.MappingProxyType(
                                                {
                                                    'nodes': (
                                                        types.MappingProxyType(
                                                            {
                                                                'commit': types.MappingProxyType(
                                                                    {
                                                                        'authoredDate': '2026-04-04T18:12:05Z'
                                                                    }
                                                                )
                                                            }
                                                        ),
                                                    )
                                                }
                                            ),
                                            'createdAt': '2026-04-04T18:24:16Z',
                                            'deletions': 36,
                                            'labels': types.MappingProxyType({'nodes': ()}),
                                            'mergedAt': '2026-04-04T18:25:39Z',
                                            'number': 53,
                                            'reviews': types.MappingProxyType({'nodes': ()}),
                                            'state': 'MERGED',
                                            'updatedAt': '2026-04-04T18:25:40Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'additions': 362,
                                            'author': types.MappingProxyType(
                                                {'__typename': 'User', 'login': 'miguelangellv'}
                                            ),
                                            'closedAt': '2026-04-04T18:12:28Z',
                                            'commits': types.MappingProxyType(
                                                {
                                                    'nodes': (
                                                        types.MappingProxyType(
                                                            {
                                                                'commit': types.MappingProxyType(
                                                                    {
                                                                        'authoredDate': '2026-04-04T17:58:30Z'
                                                                    }
                                                                )
                                                            }
                                                        ),
                                                    )
                                                }
                                            ),
                                            'createdAt': '2026-04-04T17:58:48Z',
                                            'deletions': 16,
                                            'labels': types.MappingProxyType({'nodes': ()}),
                                            'mergedAt': '2026-04-04T18:12:28Z',
                                            'number': 51,
                                            'reviews': types.MappingProxyType({'nodes': ()}),
                                            'state': 'MERGED',
                                            'updatedAt': '2026-04-04T18:12:58Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'additions': 603,
                                            'author': types.MappingProxyType(
                                                {'__typename': 'User', 'login': 'miguelangellv'}
                                            ),
                                            'closedAt': '2026-04-04T18:12:40Z',
                                            'commits': types.MappingProxyType(
                                                {
                                                    'nodes': (
                                                        types.MappingProxyType(
                                                            {
                                                                'commit': types.MappingProxyType(
                                                                    {
                                                                        'authoredDate': '2026-04-04T18:12:05Z'
                                                                    }
                                                                )
                                                            }
                                                        ),
                                                    )
                                                }
                                            ),
                                            'createdAt': '2026-04-04T18:12:14Z',
                                            'deletions': 0,
                                            'labels': types.MappingProxyType({'nodes': ()}),
                                            'mergedAt': '2026-04-04T18:12:40Z',
                                            'number': 52,
                                            'reviews': types.MappingProxyType({'nodes': ()}),
                                            'state': 'MERGED',
                                            'updatedAt': '2026-04-04T18:12:45Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'additions': 3179,
                                            'author': types.MappingProxyType(
                                                {'__typename': 'User', 'login': 'miguelangellv'}
                                            ),
                                            'closedAt': '2026-04-02T15:49:19Z',
                                            'commits': types.MappingProxyType(
                                                {
                                                    'nodes': (
                                                        types.MappingProxyType(
                                                            {
                                                                'commit': types.MappingProxyType(
                                                                    {
                                                                        'authoredDate': '2026-04-02T13:47:30Z'
                                                                    }
                                                                )
                                                            }
                                                        ),
                                                    )
                                                }
                                            ),
                                            'createdAt': '2026-04-02T14:00:08Z',
                                            'deletions': 168,
                                            'labels': types.MappingProxyType({'nodes': ()}),
                                            'mergedAt': '2026-04-02T15:49:19Z',
                                            'number': 50,
                                            'reviews': types.MappingProxyType({'nodes': ()}),
                                            'state': 'MERGED',
                                            'updatedAt': '2026-04-02T15:49:25Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'additions': 1,
                                            'author': types.MappingProxyType(
                                                {'__typename': 'User', 'login': 'sheaur'}
                                            ),
                                            'closedAt': '2026-02-28T14:55:45Z',
                                            'commits': types.MappingProxyType(
                                                {
                                                    'nodes': (
                                                        types.MappingProxyType(
                                                            {
                                                                'commit': types.MappingProxyType(
                                                                    {
                                                                        'authoredDate': '2026-02-28T14:53:49Z'
                                                                    }
                                                                )
                                                            }
                                                        ),
                                                    )
                                                }
                                            ),
                                            'createdAt': '2026-02-28T14:54:25Z',
                                            'deletions': 1,
                                            'labels': types.MappingProxyType({'nodes': ()}),
                                            'mergedAt': '2026-02-28T14:55:45Z',
                                            'number': 47,
                                            'reviews': types.MappingProxyType({'nodes': ()}),
                                            'state': 'MERGED',
                                            'updatedAt': '2026-02-28T14:55:45Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'additions': 5,
                                            'author': types.MappingProxyType(
                                                {'__typename': 'User', 'login': 'sheaur'}
                                            ),
                                            'closedAt': '2026-02-28T14:15:03Z',
                                            'commits': types.MappingProxyType(
                                                {
                                                    'nodes': (
                                                        types.MappingProxyType(
                                                            {
                                                                'commit': types.MappingProxyType(
                                                                    {
                                                                        'authoredDate': '2026-02-24T21:06:07Z'
                                                                    }
                                                                )
                                                            }
                                                        ),
                                                    )
                                                }
                                            ),
                                            'createdAt': '2026-02-24T21:06:20Z',
                                            'deletions': 6,
                                            'labels': types.MappingProxyType({'nodes': ()}),
                                            'mergedAt': '2026-02-28T14:15:03Z',
                                            'number': 46,
                                            'reviews': types.MappingProxyType({'nodes': ()}),
                                            'state': 'MERGED',
                                            'updatedAt': '2026-02-28T14:15:03Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'additions': 93,
                                            'author': types.MappingProxyType(
                                                {'__typename': 'User', 'login': 'sheaur'}
                                            ),
                                            'closedAt': '2026-02-24T21:11:43Z',
                                            'commits': types.MappingProxyType(
                                                {
                                                    'nodes': (
                                                        types.MappingProxyType(
                                                            {
                                                                'commit': types.MappingProxyType(
                                                                    {
                                                                        'authoredDate': '2026-01-16T22:35:02Z'
                                                                    }
                                                                )
                                                            }
                                                        ),
                                                    )
                                                }
                                            ),
                                            'createdAt': '2026-01-16T22:35:16Z',
                                            'deletions': 69,
                                            'labels': types.MappingProxyType({'nodes': ()}),
                                            'mergedAt': None,
                                            'number': 44,
                                            'reviews': types.MappingProxyType(
                                                {
                                                    'nodes': (
                                                        types.MappingProxyType(
                                                            {
                                                                'author': types.MappingProxyType(
                                                                    {
                                                                        '__typename': 'Bot',
                                                                        'login': 'copilot-pull-request-reviewer',
                                                                    }
                                                                ),
                                                                'submittedAt': '2026-02-24T19:26:28Z',
                                                            }
                                                        ),
                                                    )
                                                }
                                            ),
                                            'state': 'CLOSED',
                                            'updatedAt': '2026-02-25T18:10:52Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'additions': 42,
                                            'author': types.MappingProxyType(
                                                {'__typename': 'User', 'login': 'sheaur'}
                                            ),
                                            'closedAt': '2026-02-24T21:11:33Z',
                                            'commits': types.MappingProxyType(
                                                {
                                                    'nodes': (
                                                        types.MappingProxyType(
                                                            {
                                                                'commit': types.MappingProxyType(
                                                                    {
                                                                        'authoredDate': '2026-02-24T19:33:38Z'
                                                                    }
                                                                )
                                                            }
                                                        ),
                                                    )
                                                }
                                            ),
                                            'createdAt': '2026-02-24T19:34:07Z',
                                            'deletions': 17,
                                            'labels': types.MappingProxyType({'nodes': ()}),
                                            'mergedAt': None,
                                            'number': 45,
                                            'reviews': types.MappingProxyType(
                                                {
                                                    'nodes': (
                                                        types.MappingProxyType(
                                                            {
                                                                'author': types.MappingProxyType(
                                                                    {
                                                                        '__typename': 'User',
                                                                        'login': 'sheaur',
                                                                    }
                                                                ),
                                                                'submittedAt': '2026-02-24T19:48:22Z',
                                                            }
                                                        ),
                                                    )
                                                }
                                            ),
                                            'state': 'CLOSED',
                                            'updatedAt': '2026-02-24T21:11:33Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'additions': 7,
                                            'author': types.MappingProxyType(
                                                {'__typename': 'User', 'login': 'sheaur'}
                                            ),
                                            'closedAt': '2026-01-16T22:34:07Z',
                                            'commits': types.MappingProxyType(
                                                {
                                                    'nodes': (
                                                        types.MappingProxyType(
                                                            {
                                                                'commit': types.MappingProxyType(
                                                                    {
                                                                        'authoredDate': '2026-01-16T22:26:58Z'
                                                                    }
                                                                )
                                                            }
                                                        ),
                                                    )
                                                }
                                            ),
                                            'createdAt': '2026-01-16T22:27:11Z',
                                            'deletions': 9,
                                            'labels': types.MappingProxyType({'nodes': ()}),
                                            'mergedAt': None,
                                            'number': 43,
                                            'reviews': types.MappingProxyType({'nodes': ()}),
                                            'state': 'CLOSED',
                                            'updatedAt': '2026-01-16T22:34:07Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'additions': 31,
                                            'author': types.MappingProxyType(
                                                {'__typename': 'User', 'login': 'sheaur'}
                                            ),
                                            'closedAt': '2026-01-16T22:25:09Z',
                                            'commits': types.MappingProxyType(
                                                {
                                                    'nodes': (
                                                        types.MappingProxyType(
                                                            {
                                                                'commit': types.MappingProxyType(
                                                                    {
                                                                        'authoredDate': '2026-01-16T20:25:22Z'
                                                                    }
                                                                )
                                                            }
                                                        ),
                                                    )
                                                }
                                            ),
                                            'createdAt': '2026-01-16T20:25:56Z',
                                            'deletions': 14,
                                            'labels': types.MappingProxyType({'nodes': ()}),
                                            'mergedAt': None,
                                            'number': 42,
                                            'reviews': types.MappingProxyType(
                                                {
                                                    'nodes': (
                                                        types.MappingProxyType(
                                                            {
                                                                'author': types.MappingProxyType(
                                                                    {
                                                                        '__typename': 'User',
                                                                        'login': 'sheaur',
                                                                    }
                                                                ),
                                                                'submittedAt': '2026-01-16T21:50:18Z',
                                                            }
                                                        ),
                                                    )
                                                }
                                            ),
                                            'state': 'CLOSED',
                                            'updatedAt': '2026-01-16T22:25:09Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'additions': 87,
                                            'author': types.MappingProxyType(
                                                {'__typename': 'User', 'login': 'sheaur'}
                                            ),
                                            'closedAt': '2026-01-16T11:16:48Z',
                                            'commits': types.MappingProxyType(
                                                {
                                                    'nodes': (
                                                        types.MappingProxyType(
                                                            {
                                                                'commit': types.MappingProxyType(
                                                                    {
                                                                        'authoredDate': '2026-01-15T17:33:58Z'
                                                                    }
                                                                )
                                                            }
                                                        ),
                                                    )
                                                }
                                            ),
                                            'createdAt': '2026-01-15T17:34:22Z',
                                            'deletions': 59,
                                            'labels': types.MappingProxyType({'nodes': ()}),
                                            'mergedAt': None,
                                            'number': 41,
                                            'reviews': types.MappingProxyType(
                                                {
                                                    'nodes': (
                                                        types.MappingProxyType(
                                                            {
                                                                'author': types.MappingProxyType(
                                                                    {
                                                                        '__typename': 'User',
                                                                        'login': 'sheaur',
                                                                    }
                                                                ),
                                                                'submittedAt': '2026-01-15T17:53:28Z',
                                                            }
                                                        ),
                                                        types.MappingProxyType(
                                                            {
                                                                'author': types.MappingProxyType(
                                                                    {
                                                                        '__typename': 'User',
                                                                        'login': 'sheaur',
                                                                    }
                                                                ),
                                                                'submittedAt': '2026-01-15T17:57:15Z',
                                                            }
                                                        ),
                                                        types.MappingProxyType(
                                                            {
                                                                'author': types.MappingProxyType(
                                                                    {
                                                                        '__typename': 'User',
                                                                        'login': 'sheaur',
                                                                    }
                                                                ),
                                                                'submittedAt': '2026-01-15T18:04:32Z',
                                                            }
                                                        ),
                                                        types.MappingProxyType(
                                                            {
                                                                'author': types.MappingProxyType(
                                                                    {
                                                                        '__typename': 'User',
                                                                        'login': 'sheaur',
                                                                    }
                                                                ),
                                                                'submittedAt': '2026-01-15T18:11:59Z',
                                                            }
                                                        ),
                                                        types.MappingProxyType(
                                                            {
                                                                'author': types.MappingProxyType(
                                                                    {
                                                                        '__typename': 'User',
                                                                        'login': 'sheaur',
                                                                    }
                                                                ),
                                                                'submittedAt': '2026-01-15T18:16:41Z',
                                                            }
                                                        ),
                                                    )
                                                }
                                            ),
                                            'state': 'CLOSED',
                                            'updatedAt': '2026-01-16T11:16:48Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'additions': 2421,
                                            'author': types.MappingProxyType(
                                                {'__typename': 'User', 'login': 'miguelangellv'}
                                            ),
                                            'closedAt': '2025-03-17T14:47:42Z',
                                            'commits': types.MappingProxyType(
                                                {
                                                    'nodes': (
                                                        types.MappingProxyType(
                                                            {
                                                                'commit': types.MappingProxyType(
                                                                    {
                                                                        'authoredDate': '2025-03-16T21:39:49Z'
                                                                    }
                                                                )
                                                            }
                                                        ),
                                                    )
                                                }
                                            ),
                                            'createdAt': '2025-03-17T11:28:18Z',
                                            'deletions': 283,
                                            'labels': types.MappingProxyType({'nodes': ()}),
                                            'mergedAt': '2025-03-17T14:47:42Z',
                                            'number': 28,
                                            'reviews': types.MappingProxyType({'nodes': ()}),
                                            'state': 'MERGED',
                                            'updatedAt': '2025-03-17T14:47:53Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'additions': 2513,
                                            'author': types.MappingProxyType(
                                                {'__typename': 'User', 'login': 'miguelangellv'}
                                            ),
                                            'closedAt': '2025-03-16T22:05:45Z',
                                            'commits': types.MappingProxyType(
                                                {
                                                    'nodes': (
                                                        types.MappingProxyType(
                                                            {
                                                                'commit': types.MappingProxyType(
                                                                    {
                                                                        'authoredDate': '2025-03-16T21:39:49Z'
                                                                    }
                                                                )
                                                            }
                                                        ),
                                                    )
                                                }
                                            ),
                                            'createdAt': '2025-03-16T21:40:37Z',
                                            'deletions': 379,
                                            'labels': types.MappingProxyType({'nodes': ()}),
                                            'mergedAt': '2025-03-16T22:05:45Z',
                                            'number': 27,
                                            'reviews': types.MappingProxyType({'nodes': ()}),
                                            'state': 'MERGED',
                                            'updatedAt': '2025-03-16T22:05:50Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'additions': 1,
                                            'author': types.MappingProxyType(
                                                {'__typename': 'User', 'login': 'JoseRMorales'}
                                            ),
                                            'closedAt': '2025-01-22T14:34:49Z',
                                            'commits': types.MappingProxyType(
                                                {
                                                    'nodes': (
                                                        types.MappingProxyType(
                                                            {
                                                                'commit': types.MappingProxyType(
                                                                    {
                                                                        'authoredDate': '2025-01-04T16:27:34Z'
                                                                    }
                                                                )
                                                            }
                                                        ),
                                                    )
                                                }
                                            ),
                                            'createdAt': '2025-01-04T16:48:27Z',
                                            'deletions': 1,
                                            'labels': types.MappingProxyType({'nodes': ()}),
                                            'mergedAt': '2025-01-22T14:34:49Z',
                                            'number': 22,
                                            'reviews': types.MappingProxyType(
                                                {
                                                    'nodes': (
                                                        types.MappingProxyType(
                                                            {
                                                                'author': types.MappingProxyType(
                                                                    {
                                                                        '__typename': 'User',
                                                                        'login': 'polamoros',
                                                                    }
                                                                ),
                                                                'submittedAt': '2025-01-22T14:17:44Z',
                                                            }
                                                        ),
                                                    )
                                                }
                                            ),
                                            'state': 'MERGED',
                                            'updatedAt': '2025-01-22T14:35:36Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'additions': 5,
                                            'author': types.MappingProxyType(
                                                {'__typename': 'User', 'login': 'sheaur'}
                                            ),
                                            'closedAt': '2024-12-19T20:03:23Z',
                                            'commits': types.MappingProxyType(
                                                {
                                                    'nodes': (
                                                        types.MappingProxyType(
                                                            {
                                                                'commit': types.MappingProxyType(
                                                                    {
                                                                        'authoredDate': '2024-05-09T01:40:54Z'
                                                                    }
                                                                )
                                                            }
                                                        ),
                                                    )
                                                }
                                            ),
                                            'createdAt': '2024-05-09T23:29:07Z',
                                            'deletions': 5,
                                            'labels': types.MappingProxyType({'nodes': ()}),
                                            'mergedAt': '2024-12-19T20:03:23Z',
                                            'number': 14,
                                            'reviews': types.MappingProxyType({'nodes': ()}),
                                            'state': 'MERGED',
                                            'updatedAt': '2024-12-19T20:03:24Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'additions': 2,
                                            'author': types.MappingProxyType(
                                                {'__typename': 'User', 'login': 'sheaur'}
                                            ),
                                            'closedAt': '2024-12-19T20:03:12Z',
                                            'commits': types.MappingProxyType(
                                                {
                                                    'nodes': (
                                                        types.MappingProxyType(
                                                            {
                                                                'commit': types.MappingProxyType(
                                                                    {
                                                                        'authoredDate': '2024-05-10T00:58:13Z'
                                                                    }
                                                                )
                                                            }
                                                        ),
                                                    )
                                                }
                                            ),
                                            'createdAt': '2024-05-10T00:59:15Z',
                                            'deletions': 2,
                                            'labels': types.MappingProxyType({'nodes': ()}),
                                            'mergedAt': None,
                                            'number': 15,
                                            'reviews': types.MappingProxyType({'nodes': ()}),
                                            'state': 'CLOSED',
                                            'updatedAt': '2024-12-19T20:03:12Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'additions': 53,
                                            'author': types.MappingProxyType(
                                                {'__typename': 'User', 'login': 'ViPeR5000'}
                                            ),
                                            'closedAt': '2024-01-10T10:59:54Z',
                                            'commits': types.MappingProxyType(
                                                {
                                                    'nodes': (
                                                        types.MappingProxyType(
                                                            {
                                                                'commit': types.MappingProxyType(
                                                                    {
                                                                        'authoredDate': '2024-01-10T10:57:57Z'
                                                                    }
                                                                )
                                                            }
                                                        ),
                                                    )
                                                }
                                            ),
                                            'createdAt': '2024-01-10T10:58:02Z',
                                            'deletions': 0,
                                            'labels': types.MappingProxyType({'nodes': ()}),
                                            'mergedAt': '2024-01-10T10:59:54Z',
                                            'number': 10,
                                            'reviews': types.MappingProxyType({'nodes': ()}),
                                            'state': 'MERGED',
                                            'updatedAt': '2024-01-10T11:00:01Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'additions': 1,
                                            'author': types.MappingProxyType(
                                                {'__typename': 'User', 'login': 'JNP2020'}
                                            ),
                                            'closedAt': '2024-01-05T20:33:50Z',
                                            'commits': types.MappingProxyType(
                                                {
                                                    'nodes': (
                                                        types.MappingProxyType(
                                                            {
                                                                'commit': types.MappingProxyType(
                                                                    {
                                                                        'authoredDate': '2024-01-05T20:00:09Z'
                                                                    }
                                                                )
                                                            }
                                                        ),
                                                    )
                                                }
                                            ),
                                            'createdAt': '2024-01-05T20:01:07Z',
                                            'deletions': 1,
                                            'labels': types.MappingProxyType({'nodes': ()}),
                                            'mergedAt': '2024-01-05T20:33:50Z',
                                            'number': 8,
                                            'reviews': types.MappingProxyType(
                                                {
                                                    'nodes': (
                                                        types.MappingProxyType(
                                                            {
                                                                'author': types.MappingProxyType(
                                                                    {
                                                                        '__typename': 'User',
                                                                        'login': 'miguelangellv',
                                                                    }
                                                                ),
                                                                'submittedAt': '2024-01-05T20:33:42Z',
                                                            }
                                                        ),
                                                    )
                                                }
                                            ),
                                            'state': 'MERGED',
                                            'updatedAt': '2024-01-05T20:33:51Z',
                                        }
                                    ),
                                ),
                                'pageInfo': types.MappingProxyType(
                                    {
                                        'endCursor': 'Y3Vyc29yOnYyOpK0MjAyNC0wMS0wNVQyMDozMzo1MVrOY1hunQ==',
                                        'hasNextPage': False,
                                    }
                                ),
                            }
                        )
                    }
                ),
            }
        )
    }
)

ISSUES_OK = types.MappingProxyType(
    {
        'data': types.MappingProxyType(
            {
                'rateLimit': types.MappingProxyType(
                    {'cost': 1, 'remaining': 4896, 'resetAt': '2026-10-31T09:13:32Z'}
                ),
                'repository': types.MappingProxyType(
                    {
                        'issues': types.MappingProxyType(
                            {
                                'nodes': (
                                    types.MappingProxyType(
                                        {
                                            'author': types.MappingProxyType(
                                                {'__typename': 'User', 'login': 'githchema'}
                                            ),
                                            'closedAt': None,
                                            'createdAt': '2026-08-18T10:26:03Z',
                                            'number': 56,
                                            'state': 'OPEN',
                                            'updatedAt': '2026-08-18T11:06:20Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'author': types.MappingProxyType(
                                                {'__typename': 'User', 'login': 'JAIMEHVLOFT'}
                                            ),
                                            'closedAt': '2026-04-16T11:02:50Z',
                                            'createdAt': '2026-03-12T22:19:42Z',
                                            'number': 48,
                                            'state': 'CLOSED',
                                            'updatedAt': '2026-04-16T11:02:50Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'author': types.MappingProxyType(
                                                {'__typename': 'User', 'login': 'franito16'}
                                            ),
                                            'closedAt': '2026-04-16T11:02:23Z',
                                            'createdAt': '2026-04-15T04:54:00Z',
                                            'number': 55,
                                            'state': 'CLOSED',
                                            'updatedAt': '2026-04-16T11:02:23Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'author': types.MappingProxyType(
                                                {'__typename': 'User', 'login': 'GeiserX'}
                                            ),
                                            'closedAt': '2026-04-02T09:39:07Z',
                                            'createdAt': '2026-03-21T09:45:20Z',
                                            'number': 49,
                                            'state': 'CLOSED',
                                            'updatedAt': '2026-04-02T09:39:07Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'author': types.MappingProxyType(
                                                {'__typename': 'User', 'login': 'sheaur'}
                                            ),
                                            'closedAt': '2026-02-28T14:41:09Z',
                                            'createdAt': '2026-01-12T14:36:58Z',
                                            'number': 40,
                                            'state': 'CLOSED',
                                            'updatedAt': '2026-02-28T14:41:09Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'author': types.MappingProxyType(
                                                {'__typename': 'User', 'login': 'ibratos'}
                                            ),
                                            'closedAt': '2025-10-31T07:09:24Z',
                                            'createdAt': '2025-08-29T08:56:17Z',
                                            'number': 36,
                                            'state': 'CLOSED',
                                            'updatedAt': '2025-11-16T17:52:41Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'author': types.MappingProxyType(
                                                {'__typename': 'User', 'login': 'cnecrea'}
                                            ),
                                            'closedAt': None,
                                            'createdAt': '2024-01-06T03:31:58Z',
                                            'number': 9,
                                            'state': 'OPEN',
                                            'updatedAt': '2025-11-13T13:51:08Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'author': types.MappingProxyType(
                                                {'__typename': 'User', 'login': 'buckiebass'}
                                            ),
                                            'closedAt': '2025-11-04T08:37:41Z',
                                            'createdAt': '2025-07-22T10:59:04Z',
                                            'number': 35,
                                            'state': 'CLOSED',
                                            'updatedAt': '2025-11-04T08:37:41Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'author': types.MappingProxyType(
                                                {'__typename': 'User', 'login': 'marioJR1979'}
                                            ),
                                            'closedAt': '2025-10-31T07:09:54Z',
                                            'createdAt': '2025-09-04T09:09:56Z',
                                            'number': 37,
                                            'state': 'CLOSED',
                                            'updatedAt': '2025-10-31T07:09:54Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'author': types.MappingProxyType(
                                                {'__typename': 'User', 'login': 'DelBierzo'}
                                            ),
                                            'closedAt': '2025-10-31T07:09:34Z',
                                            'createdAt': '2025-10-29T16:11:17Z',
                                            'number': 38,
                                            'state': 'CLOSED',
                                            'updatedAt': '2025-10-31T07:09:34Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'author': types.MappingProxyType(
                                                {'__typename': 'User', 'login': 'ggonmar'}
                                            ),
                                            'closedAt': '2025-07-15T06:00:47Z',
                                            'createdAt': '2025-07-07T22:31:37Z',
                                            'number': 33,
                                            'state': 'CLOSED',
                                            'updatedAt': '2025-07-15T06:00:47Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'author': types.MappingProxyType(
                                                {'__typename': 'User', 'login': 'jflorido94'}
                                            ),
                                            'closedAt': '2025-07-15T05:59:48Z',
                                            'createdAt': '2025-07-15T05:57:47Z',
                                            'number': 34,
                                            'state': 'CLOSED',
                                            'updatedAt': '2025-07-15T05:59:48Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'author': types.MappingProxyType(
                                                {'__typename': 'User', 'login': 'davidpassola'}
                                            ),
                                            'closedAt': '2025-06-18T05:47:15Z',
                                            'createdAt': '2025-06-09T17:18:11Z',
                                            'number': 32,
                                            'state': 'CLOSED',
                                            'updatedAt': '2025-06-18T05:47:15Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'author': types.MappingProxyType(
                                                {'__typename': 'User', 'login': 'Drums7'}
                                            ),
                                            'closedAt': '2025-05-22T07:10:22Z',
                                            'createdAt': '2025-05-22T07:08:18Z',
                                            'number': 31,
                                            'state': 'CLOSED',
                                            'updatedAt': '2025-05-22T09:12:23Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'author': types.MappingProxyType(
                                                {'__typename': 'User', 'login': 'acopen'}
                                            ),
                                            'closedAt': '2025-04-29T07:36:07Z',
                                            'createdAt': '2025-04-29T07:32:51Z',
                                            'number': 30,
                                            'state': 'CLOSED',
                                            'updatedAt': '2025-04-29T07:36:08Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'author': types.MappingProxyType(
                                                {'__typename': 'User', 'login': 'ldsmovil'}
                                            ),
                                            'closedAt': '2025-03-25T21:13:18Z',
                                            'createdAt': '2025-03-21T13:46:30Z',
                                            'number': 29,
                                            'state': 'CLOSED',
                                            'updatedAt': '2025-03-25T21:13:19Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'author': types.MappingProxyType(
                                                {'__typename': 'User', 'login': 'Phrana'}
                                            ),
                                            'closedAt': '2025-03-17T14:49:20Z',
                                            'createdAt': '2025-02-21T07:42:24Z',
                                            'number': 24,
                                            'state': 'CLOSED',
                                            'updatedAt': '2025-03-17T22:53:53Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'author': types.MappingProxyType(
                                                {'__typename': 'User', 'login': 'marioJR1979'}
                                            ),
                                            'closedAt': '2025-03-17T14:48:56Z',
                                            'createdAt': '2025-03-12T12:49:38Z',
                                            'number': 26,
                                            'state': 'CLOSED',
                                            'updatedAt': '2025-03-17T22:46:38Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'author': types.MappingProxyType(
                                                {'__typename': 'User', 'login': 'reagnon'}
                                            ),
                                            'closedAt': '2025-03-17T15:00:24Z',
                                            'createdAt': '2025-02-11T10:23:44Z',
                                            'number': 23,
                                            'state': 'CLOSED',
                                            'updatedAt': '2025-03-17T15:00:25Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'author': types.MappingProxyType(
                                                {'__typename': 'User', 'login': 'ramonLoureiro'}
                                            ),
                                            'closedAt': '2025-03-17T14:51:23Z',
                                            'createdAt': '2025-01-02T08:32:43Z',
                                            'number': 20,
                                            'state': 'CLOSED',
                                            'updatedAt': '2025-03-17T14:51:24Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'author': types.MappingProxyType(
                                                {'__typename': 'User', 'login': 'ramonLoureiro'}
                                            ),
                                            'closedAt': '2025-03-17T14:50:25Z',
                                            'createdAt': '2025-01-02T08:37:43Z',
                                            'number': 21,
                                            'state': 'CLOSED',
                                            'updatedAt': '2025-03-17T14:50:26Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'author': types.MappingProxyType(
                                                {'__typename': 'User', 'login': 'kitopopo'}
                                            ),
                                            'closedAt': '2025-03-17T14:49:09Z',
                                            'createdAt': '2025-02-25T18:54:24Z',
                                            'number': 25,
                                            'state': 'CLOSED',
                                            'updatedAt': '2025-03-17T14:49:09Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'author': types.MappingProxyType(
                                                {'__typename': 'User', 'login': 'ivanhuert'}
                                            ),
                                            'closedAt': '2025-01-14T17:02:50Z',
                                            'createdAt': '2025-01-01T18:55:38Z',
                                            'number': 19,
                                            'state': 'CLOSED',
                                            'updatedAt': '2025-01-14T17:02:50Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'author': types.MappingProxyType(
                                                {'__typename': 'User', 'login': 'kitopopo'}
                                            ),
                                            'closedAt': '2024-12-18T18:05:45Z',
                                            'createdAt': '2024-12-15T22:31:19Z',
                                            'number': 18,
                                            'state': 'CLOSED',
                                            'updatedAt': '2024-12-19T20:00:26Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'author': types.MappingProxyType(
                                                {'__typename': 'User', 'login': 'sheaur'}
                                            ),
                                            'closedAt': '2024-12-18T18:05:44Z',
                                            'createdAt': '2024-01-13T01:46:25Z',
                                            'number': 11,
                                            'state': 'CLOSED',
                                            'updatedAt': '2024-12-19T06:50:58Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'author': types.MappingProxyType(
                                                {'__typename': 'User', 'login': 'kitopopo'}
                                            ),
                                            'closedAt': '2024-12-12T20:54:05Z',
                                            'createdAt': '2024-12-12T19:42:50Z',
                                            'number': 17,
                                            'state': 'CLOSED',
                                            'updatedAt': '2024-12-14T13:11:59Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'author': types.MappingProxyType(
                                                {'__typename': 'User', 'login': 'ppnacho'}
                                            ),
                                            'closedAt': '2024-12-13T08:37:53Z',
                                            'createdAt': '2024-10-03T20:43:55Z',
                                            'number': 16,
                                            'state': 'CLOSED',
                                            'updatedAt': '2024-12-13T08:37:53Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'author': types.MappingProxyType(
                                                {'__typename': 'User', 'login': 'sergey08'}
                                            ),
                                            'closedAt': '2024-03-23T05:28:21Z',
                                            'createdAt': '2024-02-12T18:15:15Z',
                                            'number': 13,
                                            'state': 'CLOSED',
                                            'updatedAt': '2024-03-23T05:28:21Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'author': types.MappingProxyType(
                                                {'__typename': 'User', 'login': 'PeteLawler'}
                                            ),
                                            'closedAt': '2024-01-29T20:40:21Z',
                                            'createdAt': '2024-01-29T20:27:13Z',
                                            'number': 12,
                                            'state': 'CLOSED',
                                            'updatedAt': '2024-01-29T20:49:58Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'author': types.MappingProxyType(
                                                {'__typename': 'User', 'login': 'franlauma'}
                                            ),
                                            'closedAt': '2024-01-10T11:00:12Z',
                                            'createdAt': '2024-01-02T16:19:53Z',
                                            'number': 7,
                                            'state': 'CLOSED',
                                            'updatedAt': '2024-01-10T11:00:12Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'author': types.MappingProxyType(
                                                {'__typename': 'User', 'login': 'sheaur'}
                                            ),
                                            'closedAt': '2023-12-01T07:33:40Z',
                                            'createdAt': '2023-12-01T04:50:40Z',
                                            'number': 6,
                                            'state': 'CLOSED',
                                            'updatedAt': '2023-12-01T07:33:40Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'author': types.MappingProxyType(
                                                {'__typename': 'User', 'login': 'cbolumar'}
                                            ),
                                            'closedAt': '2023-10-15T16:40:50Z',
                                            'createdAt': '2023-10-09T17:48:35Z',
                                            'number': 5,
                                            'state': 'CLOSED',
                                            'updatedAt': '2023-10-17T19:58:07Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'author': types.MappingProxyType(
                                                {'__typename': 'User', 'login': 'tergontor'}
                                            ),
                                            'closedAt': '2023-10-15T16:40:58Z',
                                            'createdAt': '2023-10-08T14:12:14Z',
                                            'number': 1,
                                            'state': 'CLOSED',
                                            'updatedAt': '2023-10-16T18:06:42Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'author': types.MappingProxyType(
                                                {'__typename': 'User', 'login': 'cbolumar'}
                                            ),
                                            'closedAt': '2023-10-09T17:38:52Z',
                                            'createdAt': '2023-10-09T17:37:39Z',
                                            'number': 4,
                                            'state': 'CLOSED',
                                            'updatedAt': '2023-10-09T17:39:41Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'author': types.MappingProxyType(
                                                {'__typename': 'User', 'login': 'sergey08'}
                                            ),
                                            'closedAt': '2023-10-09T11:15:43Z',
                                            'createdAt': '2023-10-09T08:31:36Z',
                                            'number': 2,
                                            'state': 'CLOSED',
                                            'updatedAt': '2023-10-09T11:15:43Z',
                                        }
                                    ),
                                ),
                                'pageInfo': types.MappingProxyType(
                                    {
                                        'endCursor': 'Y3Vyc29yOnYyOpK0MjAyMy0xMC0wOVQxMToxNTo0M1rOczB6Jw==',
                                        'hasNextPage': False,
                                    }
                                ),
                            }
                        )
                    }
                ),
            }
        )
    }
)

RELEASES_OK = types.MappingProxyType(
    {
        'data': types.MappingProxyType(
            {
                'rateLimit': types.MappingProxyType(
                    {'cost': 1, 'remaining': 4668, 'resetAt': '2026-10-31T09:13:32Z'}
                ),
                'repository': types.MappingProxyType(
                    {
                        'releases': types.MappingProxyType(
                            {
                                'nodes': (
                                    types.MappingProxyType(
                                        {
                                            'createdAt': '2026-04-04T18:30:38Z',
                                            'isDraft': False,
                                            'isPrerelease': False,
                                            'publishedAt': '2026-04-04T18:30:39Z',
                                            'tagName': 'v2.3.1',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'createdAt': '2026-04-02T15:49:19Z',
                                            'isDraft': False,
                                            'isPrerelease': False,
                                            'publishedAt': '2026-04-02T15:50:48Z',
                                            'tagName': 'V2.3',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'createdAt': '2026-02-28T14:55:45Z',
                                            'isDraft': False,
                                            'isPrerelease': False,
                                            'publishedAt': '2026-02-28T14:56:41Z',
                                            'tagName': 'V2.2',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'createdAt': '2025-10-31T07:07:57Z',
                                            'isDraft': False,
                                            'isPrerelease': False,
                                            'publishedAt': '2025-10-31T07:09:03Z',
                                            'tagName': 'V2.1',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'createdAt': '2025-03-17T14:47:42Z',
                                            'isDraft': False,
                                            'isPrerelease': False,
                                            'publishedAt': '2025-03-17T14:48:27Z',
                                            'tagName': 'V2.0',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'createdAt': '2025-03-17T11:28:04Z',
                                            'isDraft': False,
                                            'isPrerelease': True,
                                            'publishedAt': '2025-03-17T11:29:53Z',
                                            'tagName': 'V2.0-Beta',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'createdAt': '2024-12-18T18:03:54Z',
                                            'isDraft': False,
                                            'isPrerelease': False,
                                            'publishedAt': '2024-12-18T18:04:59Z',
                                            'tagName': 'V1.4',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'createdAt': '2023-10-14T06:03:13Z',
                                            'isDraft': False,
                                            'isPrerelease': False,
                                            'publishedAt': '2023-10-15T16:43:20Z',
                                            'tagName': 'V1.3',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'createdAt': '2023-10-09T17:41:23Z',
                                            'isDraft': False,
                                            'isPrerelease': False,
                                            'publishedAt': '2023-10-09T17:42:44Z',
                                            'tagName': 'V1.2',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'createdAt': '2023-10-09T11:13:53Z',
                                            'isDraft': False,
                                            'isPrerelease': False,
                                            'publishedAt': '2023-10-09T11:15:12Z',
                                            'tagName': '1.1',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'createdAt': '2023-06-19T14:59:40Z',
                                            'isDraft': False,
                                            'isPrerelease': False,
                                            'publishedAt': '2023-06-19T15:00:19Z',
                                            'tagName': '1.0',
                                        }
                                    ),
                                ),
                                'pageInfo': types.MappingProxyType(
                                    {
                                        'endCursor': 'Y3Vyc29yOnYyOpK0MjAyMy0wNi0xOVQxNDo1OTo0MFrOBoDwiQ==',
                                        'hasNextPage': False,
                                    }
                                ),
                            }
                        )
                    }
                ),
            }
        )
    }
)

WORKFLOW_RUNS_OK = types.MappingProxyType(
    {
        'total_count': 214,
        'workflow_runs': (
            types.MappingProxyType(
                {
                    'conclusion': 'skipped',
                    'created_at': '2026-10-20T16:01:52Z',
                    'event': 'pull_request',
                    'head_branch': 'frenck/add-brand-assets-gas_station_spain',
                    'id': 39453803857,
                    'name': 'Create Release and Tag',
                    'path': '.github/workflows/create-release.yml',
                    'run_attempt': 1,
                    'run_started_at': '2026-10-20T16:01:52Z',
                    'status': 'completed',
                    'updated_at': '2026-10-20T16:01:58Z',
                }
            ),
            types.MappingProxyType(
                {
                    'conclusion': 'success',
                    'created_at': '2026-10-20T16:01:51Z',
                    'event': 'push',
                    'head_branch': 'main',
                    'id': 39453802041,
                    'name': 'Tests',
                    'path': '.github/workflows/tests.yml',
                    'run_attempt': 1,
                    'run_started_at': '2026-10-20T16:01:51Z',
                    'status': 'completed',
                    'updated_at': '2026-10-20T16:02:22Z',
                }
            ),
            types.MappingProxyType(
                {
                    'conclusion': 'success',
                    'created_at': '2026-10-20T15:05:07Z',
                    'event': 'pull_request',
                    'head_branch': 'frenck/add-brand-assets-gas_station_spain',
                    'id': 39445158088,
                    'name': 'Tests',
                    'path': '.github/workflows/tests.yml',
                    'run_attempt': 2,
                    'run_started_at': '2026-10-20T16:00:22Z',
                    'status': 'completed',
                    'updated_at': '2026-10-20T16:00:50Z',
                }
            ),
            types.MappingProxyType(
                {
                    'conclusion': 'skipped',
                    'created_at': '2026-10-20T15:05:07Z',
                    'event': 'pull_request',
                    'head_branch': 'frenck/add-brand-assets-gas_station_spain',
                    'id': 39445157312,
                    'name': 'Validate Release PR',
                    'path': '.github/workflows/validate-release-pr.yml',
                    'run_attempt': 2,
                    'run_started_at': '2026-10-20T16:00:22Z',
                    'status': 'completed',
                    'updated_at': '2026-10-20T16:00:31Z',
                }
            ),
            types.MappingProxyType(
                {
                    'conclusion': 'success',
                    'created_at': '2026-10-20T15:05:07Z',
                    'event': 'pull_request',
                    'head_branch': 'frenck/add-brand-assets-gas_station_spain',
                    'id': 39445156073,
                    'name': 'Ruff',
                    'path': '.github/workflows/ruff.yaml',
                    'run_attempt': 2,
                    'run_started_at': '2026-10-20T16:00:22Z',
                    'status': 'completed',
                    'updated_at': '2026-10-20T16:00:46Z',
                }
            ),
        ),
    }
)

WORKFLOW_RUN_OK = types.MappingProxyType(
    {
        'conclusion': 'skipped',
        'created_at': '2026-10-20T16:01:52Z',
        'event': 'pull_request',
        'head_branch': 'frenck/add-brand-assets-gas_station_spain',
        'id': 39453803857,
        'name': 'Create Release and Tag',
        'path': '.github/workflows/create-release.yml',
        'run_attempt': 1,
        'run_started_at': '2026-10-20T16:01:52Z',
        'status': 'completed',
        'updated_at': '2026-10-20T16:01:58Z',
    }
)

STARGAZERS_OK = types.MappingProxyType(
    {
        'data': types.MappingProxyType(
            {
                'rateLimit': types.MappingProxyType(
                    {'cost': 1, 'remaining': 4895, 'resetAt': '2026-10-31T09:13:32Z'}
                ),
                'repository': types.MappingProxyType(
                    {
                        'stargazers': types.MappingProxyType(
                            {
                                'edges': (
                                    types.MappingProxyType(
                                        {
                                            'node': types.MappingProxyType(
                                                {'id': 'MDQ6VXNlcjE4NTkwMg=='}
                                            ),
                                            'starredAt': '2025-03-21T22:32:32Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'node': types.MappingProxyType(
                                                {'id': 'MDQ6VXNlcjQ2OTQ0Mjg3'}
                                            ),
                                            'starredAt': '2024-11-11T17:04:44Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'node': types.MappingProxyType(
                                                {'id': 'MDQ6VXNlcjY1OTMzMzQw'}
                                            ),
                                            'starredAt': '2023-09-21T00:41:41Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'node': types.MappingProxyType(
                                                {'id': 'MDQ6VXNlcjI4OTUwNzM2'}
                                            ),
                                            'starredAt': '2023-07-16T23:59:24Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'node': types.MappingProxyType({'id': 'U_kgDOBlkIcw'}),
                                            'starredAt': '2023-02-07T07:46:17Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'node': types.MappingProxyType(
                                                {'id': 'MDQ6VXNlcjg0NDEwNTU1'}
                                            ),
                                            'starredAt': '2022-05-15T14:39:56Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'node': types.MappingProxyType(
                                                {'id': 'MDQ6VXNlcjg1NjQ1OTE2'}
                                            ),
                                            'starredAt': '2022-03-20T17:59:21Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'node': types.MappingProxyType(
                                                {'id': 'MDQ6VXNlcjQ5MTQ1OA=='}
                                            ),
                                            'starredAt': '2021-08-14T13:53:11Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'node': types.MappingProxyType(
                                                {'id': 'MDQ6VXNlcjE1NzMwMzQ='}
                                            ),
                                            'starredAt': '2020-11-29T11:59:31Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'node': types.MappingProxyType(
                                                {'id': 'MDQ6VXNlcjM3NTg5NTE='}
                                            ),
                                            'starredAt': '2020-10-29T00:11:30Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'node': types.MappingProxyType(
                                                {'id': 'MDQ6VXNlcjUxMTA1Mg=='}
                                            ),
                                            'starredAt': '2020-08-24T15:35:22Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'node': types.MappingProxyType(
                                                {'id': 'MDQ6VXNlcjI3ODc5MA=='}
                                            ),
                                            'starredAt': '2019-09-27T09:02:42Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'node': types.MappingProxyType(
                                                {'id': 'MDQ6VXNlcjUwMDI0NTM='}
                                            ),
                                            'starredAt': '2019-07-10T04:40:12Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'node': types.MappingProxyType(
                                                {'id': 'MDQ6VXNlcjMyNDY5MDgy'}
                                            ),
                                            'starredAt': '2018-12-12T20:17:52Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'node': types.MappingProxyType(
                                                {'id': 'MDQ6VXNlcjUzOTg1NTc='}
                                            ),
                                            'starredAt': '2018-11-16T14:30:19Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'node': types.MappingProxyType(
                                                {'id': 'MDQ6VXNlcjgxMjAzNw=='}
                                            ),
                                            'starredAt': '2018-11-05T17:16:17Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'node': types.MappingProxyType(
                                                {'id': 'MDQ6VXNlcjI1MzY5Mzcy'}
                                            ),
                                            'starredAt': '2018-06-13T15:59:01Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'node': types.MappingProxyType(
                                                {'id': 'MDQ6VXNlcjEzMzY4ODE='}
                                            ),
                                            'starredAt': '2018-04-21T03:23:51Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'node': types.MappingProxyType(
                                                {'id': 'MDQ6VXNlcjY0MzcyNDM='}
                                            ),
                                            'starredAt': '2018-03-21T03:04:55Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'node': types.MappingProxyType(
                                                {'id': 'MDQ6VXNlcjUxODM0Nzc='}
                                            ),
                                            'starredAt': '2017-12-13T06:46:50Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'node': types.MappingProxyType(
                                                {'id': 'MDQ6VXNlcjUyMjI4MQ=='}
                                            ),
                                            'starredAt': '2017-08-27T19:05:01Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'node': types.MappingProxyType(
                                                {'id': 'MDQ6VXNlcjg0Mjg4NTI='}
                                            ),
                                            'starredAt': '2017-08-02T12:39:43Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'node': types.MappingProxyType(
                                                {'id': 'MDQ6VXNlcjcyMzQ1MQ=='}
                                            ),
                                            'starredAt': '2017-01-18T13:26:02Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'node': types.MappingProxyType(
                                                {'id': 'MDQ6VXNlcjc1MzcyOTY='}
                                            ),
                                            'starredAt': '2016-04-21T02:05:49Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'node': types.MappingProxyType(
                                                {'id': 'MDQ6VXNlcjE2Nzc3OTA='}
                                            ),
                                            'starredAt': '2015-11-15T08:20:18Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'node': types.MappingProxyType(
                                                {'id': 'MDQ6VXNlcjE2Nzg1NzU='}
                                            ),
                                            'starredAt': '2015-10-26T13:10:50Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'node': types.MappingProxyType(
                                                {'id': 'MDQ6VXNlcjU0MDQxNTI='}
                                            ),
                                            'starredAt': '2015-10-26T12:29:16Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'node': types.MappingProxyType(
                                                {'id': 'MDQ6VXNlcjM1OTk2ODI='}
                                            ),
                                            'starredAt': '2015-10-26T06:51:45Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'node': types.MappingProxyType(
                                                {'id': 'MDQ6VXNlcjExNTM0NzM='}
                                            ),
                                            'starredAt': '2015-10-01T09:52:55Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'node': types.MappingProxyType(
                                                {'id': 'MDQ6VXNlcjc3NTAxMw=='}
                                            ),
                                            'starredAt': '2015-09-29T01:25:42Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'node': types.MappingProxyType(
                                                {'id': 'MDQ6VXNlcjMzNTcxOQ=='}
                                            ),
                                            'starredAt': '2015-09-27T01:42:43Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'node': types.MappingProxyType(
                                                {'id': 'MDQ6VXNlcjExNDg2MDE='}
                                            ),
                                            'starredAt': '2015-09-27T01:21:13Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'node': types.MappingProxyType(
                                                {'id': 'MDQ6VXNlcjE4NDI0OQ=='}
                                            ),
                                            'starredAt': '2015-09-26T22:56:26Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'node': types.MappingProxyType(
                                                {'id': 'MDQ6VXNlcjM5NTM0MA=='}
                                            ),
                                            'starredAt': '2015-09-23T02:50:19Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'node': types.MappingProxyType(
                                                {'id': 'MDQ6VXNlcjI5OTQzNTY='}
                                            ),
                                            'starredAt': '2015-09-22T19:52:33Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'node': types.MappingProxyType(
                                                {'id': 'MDQ6VXNlcjEyMDkxNTk='}
                                            ),
                                            'starredAt': '2015-09-21T05:57:11Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'node': types.MappingProxyType(
                                                {'id': 'MDQ6VXNlcjczMzEzMA=='}
                                            ),
                                            'starredAt': '2015-09-18T16:01:11Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'node': types.MappingProxyType(
                                                {'id': 'MDQ6VXNlcjg5NTU1Mw=='}
                                            ),
                                            'starredAt': '2015-09-17T18:47:56Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'node': types.MappingProxyType(
                                                {'id': 'MDQ6VXNlcjEzNjEzODE='}
                                            ),
                                            'starredAt': '2015-09-13T00:06:37Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'node': types.MappingProxyType(
                                                {'id': 'MDQ6VXNlcjIyOTgzMjU='}
                                            ),
                                            'starredAt': '2015-09-09T07:35:01Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'node': types.MappingProxyType(
                                                {'id': 'MDQ6VXNlcjM0MjA5NQ=='}
                                            ),
                                            'starredAt': '2015-09-01T05:50:48Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'node': types.MappingProxyType(
                                                {'id': 'MDQ6VXNlcjI2OTkw'}
                                            ),
                                            'starredAt': '2015-08-30T00:37:43Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'node': types.MappingProxyType(
                                                {'id': 'MDQ6VXNlcjI3MjcyNzk='}
                                            ),
                                            'starredAt': '2015-08-06T15:46:37Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'node': types.MappingProxyType(
                                                {'id': 'MDQ6VXNlcjI5MTE0Mg=='}
                                            ),
                                            'starredAt': '2015-08-02T14:19:31Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'node': types.MappingProxyType(
                                                {'id': 'MDQ6VXNlcjY5NDY3NzI='}
                                            ),
                                            'starredAt': '2015-07-28T00:04:38Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'node': types.MappingProxyType(
                                                {'id': 'MDQ6VXNlcjI0NDcwNA=='}
                                            ),
                                            'starredAt': '2015-07-20T17:23:46Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'node': types.MappingProxyType(
                                                {'id': 'MDQ6VXNlcjE3MDY2OTU='}
                                            ),
                                            'starredAt': '2015-07-15T10:24:33Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'node': types.MappingProxyType(
                                                {'id': 'MDQ6VXNlcjE2ODc0MTg='}
                                            ),
                                            'starredAt': '2015-07-10T08:48:01Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'node': types.MappingProxyType(
                                                {'id': 'MDQ6VXNlcjQ2NTY1'}
                                            ),
                                            'starredAt': '2015-07-10T03:14:04Z',
                                        }
                                    ),
                                    types.MappingProxyType(
                                        {
                                            'node': types.MappingProxyType(
                                                {'id': 'MDQ6VXNlcjIwMTgwNA=='}
                                            ),
                                            'starredAt': '2015-06-30T08:05:56Z',
                                        }
                                    ),
                                ),
                                'pageInfo': types.MappingProxyType(
                                    {
                                        'endCursor': 'Y3Vyc29yOnYyOpK0MjAxNS0wNi0zMFQwODowNTo1NlrOAlFqQg==',
                                        'hasNextPage': False,
                                    }
                                ),
                            }
                        )
                    }
                ),
            }
        )
    }
)

FORKS_OK = (
    types.MappingProxyType({'created_at': '2024-12-18T18:28:36Z', 'id': 905394408}),
    types.MappingProxyType({'created_at': '2023-09-21T00:41:43Z', 'id': 694414618}),
    types.MappingProxyType({'created_at': '2021-10-11T21:21:18Z', 'id': 416090426}),
    types.MappingProxyType({'created_at': '2020-11-20T07:12:17Z', 'id': 314475023}),
    types.MappingProxyType({'created_at': '2019-08-01T03:13:58Z', 'id': 199967649}),
)

BOT_REVIEWS_OK = types.MappingProxyType(
    {
        'data': types.MappingProxyType(
            {
                'rateLimit': types.MappingProxyType(
                    {'cost': 1, 'remaining': 4667, 'resetAt': '2026-10-31T09:13:32Z'}
                ),
                'repository': types.MappingProxyType(
                    {
                        'pullRequest': types.MappingProxyType(
                            {
                                'reviews': types.MappingProxyType(
                                    {
                                        'nodes': (
                                            types.MappingProxyType(
                                                {
                                                    'author': types.MappingProxyType(
                                                        {
                                                            '__typename': 'Bot',
                                                            'login': 'copilot-pull-request-reviewer',
                                                        }
                                                    ),
                                                    'submittedAt': '2026-10-30T20:43:14Z',
                                                }
                                            ),
                                            types.MappingProxyType(
                                                {
                                                    'author': types.MappingProxyType(
                                                        {'__typename': 'User', 'login': 'jruales'}
                                                    ),
                                                    'submittedAt': '2026-10-31T04:36:53Z',
                                                }
                                            ),
                                        )
                                    }
                                )
                            }
                        )
                    }
                ),
            }
        )
    }
)

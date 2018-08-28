class NoRepositoryFoundError(RuntimeError):
    pass


class NonGitRepoError(RuntimeError):
    pass


class NonGithubRepoError(NonGitRepoError):
    pass


class InvalidJSONConversion(RuntimeError):
    pass


class GithubAccessLimitReachedError(RuntimeError):
    pass

# Contributing

Contributions are welcome and will be fully credited!

We accept contributions via Pull Requests on [Github](<https://github.com/{{> githubAccount }}/{{ name }}).

## Pull Requests

Here are some guidelines to make the process smoother:

- **Add a test** - New features and bugfixes need tests. Randomly breaking public APIs is not an option. If you find it difficult to test, please tell us in the pull request and we will try to help you!
- **Document any change in behavior** - Make sure the `README.md` and any other relevant documentation under `docs/**/*.md` are kept up-to-date.
- **Run `poetry run pytest tests` locally** - This will allow you to go faster
- **One pull request per feature** - If you want to do more than one thing, send multiple pull requests.
- **Send coherent history** - Make sure your commits message means something

## Creating issues

### Bug reports

Always try to provide as much information as possible. If you are reporting a bug, try to provide a example for reproduction or a stacktrace at the very least. This will help us check the problem quicker.

### Feature requests

Lay out the reasoning behind it and propose an API for it. Ideally, you should have a practical example to prove the utility of the feature you're requesting.

## Contributing Docs

All the documentation files can be found in `docs`. They are currently only Markdown files and will probably stay that way until we have a reason for updating them.

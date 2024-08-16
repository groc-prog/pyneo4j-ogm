## Git Commit Message Convention

### TL;DR

This project adopts the default guidelines provided by [`commitizen`](https://commitizen-tools.github.io/commitizen/). This is used for automatic changelog generation.

Messages must be matched by the following regex:

```text
/^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|wip)(\(.+\))?: .+/
```

#### Examples

Appears under "Features" header, `link` subheader:

```bash
feat(link): add `force` option
```

Appears under "Bug Fixes" header, `view` subheader, with a link to issue #28:

```bash
fix(view): handle keep-alive with aborted navigations

close #28
```

The following commit and commit `667ecc1` do not appear in the changelog if they are under the same release. If not, the revert commit appears under the "Reverts" header.

```bash
revert: feat(compiler): add 'comments' option

This reverts commit 667ecc1654a317a13331b17617d973392f415f02.
```

### Full Message Format

A commit message consists of a **header**, **body** and **footer**. The header has a **type**, **scope** and **subject**:

```bash
<type>(<scope>): <subject>
<BLANK LINE>
<body>
<BLANK LINE>
<footer>
```

The **header** is mandatory and the **scope** of the header is optional.

### Type

If the prefix is `feat`, `fix`, `perf` or `docs`, it will appear in the changelog.

Other prefixes are up to your discretion. Suggested prefixes are `chore`, `style`, `refactor`, and `test` for non-changelog related tasks.

### Scope

The scope could be anything specifying the place of the commit change or no scope at all for general changes. For example `client`, `node-model`, `types`, `query-builder`, `migrations` etc...

### Subject

The subject contains a succinct description of the change:

- use the imperative, present tense: "change" not "changed" nor "changes"
- don't capitalize the first letter
- no dot (.) at the end

### Body

Just as in the **subject**, use the imperative, present tense: "change" not "changed" nor "changes".
The body should include the motivation for the change and contrast this with previous behavior.

### Footer

The footer should contain any information about **Breaking Changes** and is also the place to
reference GitHub issues that this commit **Closes**.

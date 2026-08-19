# Repository selection and remote safety

This project is the canonical public implementation repository for the reusable content-production layer. The local content vault remains the source of truth for private editorial material and platform state.

## Mandatory repository-discovery gate

Before creating a repository, adding a remote, or pushing implementation code:

1. Identify the current Git root:

   ```bash
   git rev-parse --show-toplevel
   ```

2. Inspect the existing remote. An existing `origin` is authoritative unless the user explicitly directs a migration:

   ```bash
   git remote -v
   ```

3. Read the local repository `README.md`, relevant `docs/`, and the project's architecture notes. Do not infer a remote repository from a local directory name.

4. Discover the user's GitHub repositories and match by repository metadata, description, and documented architecture:

   ```bash
   gh repo list <owner> --limit 100
   ```

5. Only create a new remote when no existing repository matches, the scope is explicit, and the visibility decision is intentional. A temporary worker directory, skill directory, or experiment name is not evidence that a new GitHub repository is needed.

## Canonical placement for this project

| Material | Canonical location |
|---|---|
| Generic engines, adapters, schemas, tests, and redacted examples | this repository: `CXL-edu/article-style-system` |
| Private mother copy, real assets, credentials, account state, and publication records | local private vault under `~/media/` |
| Hermes routing rules | user-local Skill `content-video-pipeline` |

Do not copy real content packages, private paths, account identifiers, cookies, tokens, or platform screenshots into this public repository.

## Pre-push gate

Before pushing a change:

```bash
git status --short --branch
git diff --cached --check
git diff --cached --stat
git remote -v
```

Review the staged diff for:

- credentials, cookies, tokens, `.env` files, private keys, and connection strings;
- personal absolute paths and local usernames;
- real content packages, unpublished copy, media, or platform records;
- scripts that publish without an explicit local authorization policy.

Push only reviewed, tracked files. Never use a broad `git add .` as a substitute for review.

## If a wrong remote is created

Stop before pushing. Remove the accidental local remote so it cannot be reused by mistake. Do not delete the remote repository without explicit confirmation; first verify whether it is empty and whether any other work depends on it. Correct the canonical repository references in the local Skill and operating notes.

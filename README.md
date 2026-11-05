# hk-config

Extra [hk](https://hk.jdx.dev) builtins, published as a Pkl package so that any repository can import them.

hk ships a fixed set of builtins, and a config that amends hk's `Config.pkl` can only use those.
This package holds the builtins that hk does not ship.

## Use it

The package version is the hk version it targets plus a revision, such as `2.10.0-1`.
The revision exists because builtins land more often than hk releases do, so take the newest revision of the hk release you amend: `<hk-version>-<revision>`, where the first revision of an hk release is `0`.

```pkl
// hk.pkl
amends "package://github.com/nnutter/hk-config/releases/download/v<hk-version>-<revision>/hk-config@<hk-version>-<revision>#/Config.pkl"

import "package://github.com/nnutter/hk-config/releases/download/v<hk-version>-<revision>/hk-config@<hk-version>-<revision>#/Builtins.pkl" as Extra

steps {
  ["mdlint"] = Extra.mdlint
}
```

This package's `Config.pkl` amends hk's, so your config and these builtins share one hk version.
`<hk-version>` must be the hk release you amend, or the steps are different Pkl types and the config will not type-check.
Amending hk's `Config.pkl` directly also works, but then its version must equal `<hk-version>`.

## Builtins

| Name | Runs |
| --- | --- |
| `api_linter` | `api-linter --set-exit-status` on `**/*.proto` |
| `api_linter_buf` | `api-linter --set-exit-status` with a `buf build` descriptor set on `**/*.proto` |
| `constable` | `constable ./...` to check, `constable -fix ./...` to fix, both with `-sumtype.default-signifies-exhaustive=false` and `-sumtype.include-shared-interfaces`, on `**/*.go` |
| `go_imports` | `goimports -local "$(go list -m)" -l` and `-d` to check, `-w` to fix, on `**/*.go` |
| `go_generate` | `go generate ./...` to fix, on `**/*.go`, `**/*.proto`, and the buf config |
| `go_sec` | `gosec -severity high -quiet ./...` on `**/*.go` |
| `gohawk` | `gohawk ./...` on `**/*.go` |
| `mdlint` | `mdlint format --check` and `mdlint check --no-fix` to check, `mdlint format` and `mdlint check --fix` to fix, on `**/*.md` and `**/*.markdown` |
| `skills_ref` | `agentskills validate` on each `**/SKILL.md`, no fix |
| `timber_commit_msg` | `timber review commit-msg` in a `commit-msg` hook |

The Go builtins run at the `go.mod` workspace and need a Go toolchain.
`go_generate` only fixes, so a check hook skips it and the hooks that rewrite files run it first in the `go` group, before the steps that format its output.
A repository that generates from other inputs adds them to its glob.

`api_linter` runs at the working directory, which has to be the root that the protos import from: the linter resolves an import against it and ignores an `-I` path inside it.
A repository whose protos are rooted in `proto/` sets `dir = "proto"`, and the default glob then selects the files under that directory.
`api_linter` needs the imports on disk, because a buf module cache is not on the import path.

`api_linter_buf` runs the same way, at the root of a buf module, and pipes a descriptor set from `buf build` into the linter.
Buf then resolves imports from other modules, including the module cache.
It needs `buf` and `api-linter`, and it runs on bash because it uses process substitution.
The `proto` hook group keeps `api_linter`, so a consumer that selects `api_linter_buf` replaces that step.

Install the tools with mise:

```sh
mise use "github:nnutter/mdlint@latest"
mise use "go:github.com/googleapis/api-linter/cmd/api-linter@latest"
mise use "go:github.com/kojah/gohawk@latest"
mise use "go:github.com/nnutter/constable/cmd/constable@latest"
mise use "go:github.com/securego/gosec/v2/cmd/gosec@latest"
mise use "go:github.com/nnutter/timber@latest"
mise use "go:golang.org/x/tools/cmd/goimports@latest"
mise use buf@latest
mise use "pypi:agentskills-tools@latest"
mise use go@latest
```

## Hooks

`Hooks.pkl` runs a group of steps in each hook, so a consumer does not list every step itself.

```pkl
// hk.pkl
import "package://github.com/nnutter/hk-config/releases/download/v<hk-version>-<revision>/hk-config@<hk-version>-<revision>#/Hooks.pkl" as Hooks

hooks = Hooks.all(List("go", "python"))
```

`Hooks.all(groups)` builds the `check`, `fix`, `pre-commit`, and `commit-msg` hooks.
`Hooks.check(groups)`, `Hooks.fix(groups)`, `Hooks.preCommit(groups)`, and `Hooks.commitMsg()` build one hook each, for a config that sets them separately.
The argument is required because the Pkl evaluator inside hk has no default parameter values; `List()` runs the defaults alone.

Each hook runs its own default steps, and `groups` adds more.

| Hook | Default steps |
| --- | --- |
| `check` | `newlines`, `trailing_whitespace`, `pkl_format`, `pkl`, `mdlint`, `mise`, `jactionlint`, `gitleaks` over the worktree |
| `fix` | the same steps, running the fix commands |
| `pre-commit` | the same steps, with `gitleaks` over staged content, staging the fixes |
| `commit-msg` | `change-id` only, because it rewrites the message file |

`jactionlint` is hk's builtin for `jdx/jactionlint`, a maintained fork of `actionlint` that also reads composite actions and Dependabot configuration.
Its default profile checks more than `actionlint` did, and it rewrites files in the hooks that fix.
A consumer that switches to this template can therefore see findings they did not see before, and fixes applied to their workflows: set a job timeout, a concurrency group, and explicit permissions on each workflow.

## Hook groups

| Group | Steps |
| --- | --- |
| `agentskills` | `skills_ref` |
| `go` | `go_generate`, `go_imports`, `go_fumpt`, `go_fix`, `constable`, `gomod_tidy`, `go_vet`, `staticcheck`, `go_vuln_check`, `go_sec`, `gohawk` |
| `json` | `oxfmt` over `json`, `jsonc`, `json5` |
| `proto` | `buf_format`, `buf_lint`, `api_linter` |
| `python` | `ruff_format`, `ruff`, `ty` |
| `rust` | `cargo_fmt`, `cargo_check`, `cargo_clippy` |
| `shell` | `shfmt`, `shellcheck` |
| `toml` | `tombi_format`, `tombi` |
| `ts-backend` | `oxfmt`, `ox_lint`, `tsc` over `ts`, `mts`, `cts`, `js`, `mjs`, `cjs` |
| `ts-frontend` | `oxfmt`, `ox_lint` over `jsx`, `tsx`, `vue`, `svelte`, `mdx`, `astro` |
| `yaml` | `yamlfmt` |

The `go` group's `constable` step embeds `testifylint` v0.0.1, while the removed `testifylint` pin named an older build of the fork.
Version 0.0.1 also reports `useless-assert`, so a fix hook can exit 3 after `constable -fix` rewrites an assertion such as `assert.Equal(t, true, false)` to `assert.True(t, false)`.
The developer must then change the assertion.

A misspelled group fails the config with the list of group names.

`fix` and `pre-commit` set `depends` inside each group: the steps that rewrite files form a chain, and every step that only reads waits for the last fixer and for no other reader, so the readers run together.
The default steps order the same way: `newlines` then `trailing_whitespace`, and then `pkl_format`, `mdlint`, `mise`, and `jactionlint` each wait only for `trailing_whitespace`, while `pkl` waits for `pkl_format` and `gitleaks` waits for `jactionlint`, the last default step that rewrites files.
Groups have no `depends` between them, so they run at the same time when their file selections differ. hk's file locks still serialize steps that select the same file, which is why `newlines` and `trailing_whitespace` — both select every text file — wait for each other. `check` sets no `depends`, so every step runs at once.

A consumer adds a step after the template, and drops a default step with hk's own setting:

```pkl
hooks = (Hooks.all(List("go"))) {
  ["pre-commit"] {
    steps {
      ["own"] = new Step {
        glob = List("**/*.txt")
        check = "true"
      }
    }
  }
}

skip_steps = List("jactionlint")
```

hk's `oxfmt` builtin selects Markdown, YAML, TOML, JSON, HTML, and CSS as well as JavaScript and
TypeScript.
The template narrows a copy for each group, because two groups must not format the same file.

## Releases

A tag names a package version, so `v2.10.0-1` is the second release against hk 2.10.0.
The tags are the ledger: `scripts/update-hk` reads the tags of the pinned hk version to name the version to publish next.

To publish a revision of the pinned hk release:

```sh
version=$(scripts/update-hk)
git tag "v$version"
git push origin "v$version"
```

To move to another hk release, pass it: `scripts/update-hk 2.11.0` pins it and prints `2.11.0-0`.
Tag the version it prints, and the update workflow does the same on the schedule that follows hk releases.

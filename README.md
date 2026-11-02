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
| `constable` | `constable ./...` to check, `constable -fix ./...` to fix, on `**/*.go` |
| `go_check_sumtype` | `go-check-sumtype -default-signifies-exhaustive=false -include-shared-interfaces ./...` on `**/*.go` |
| `go_fix` | `go fix -diff ./...` to check, no fix, on `**/*.go` |
| `go_imports` | `goimports -local "$(go list -m)" -l` and `-d` to check, `-w` to fix, on `**/*.go` |
| `go_sec` | `gosec -severity high -quiet ./...` on `**/*.go` |
| `gohawk` | `gohawk ./...` on `**/*.go` |
| `gomod_tidy` | `go mod tidy -diff` to check, no fix, on `**/*.go`, `**/go.mod`, and `**/go.sum` |
| `mdlint` | `mdlint format --check` and `mdlint check --no-fix` to check, `mdlint format` and `mdlint check --fix` to fix, on `**/*.md` and `**/*.markdown` |
| `nilaway` | `nilaway -include-pkgs $(go list -m) ./...` on `**/*.go` |
| `testifylint` | `testifylint ./...` to check, `testifylint -fix ./...` to fix, on `**/*.go` |
| `timber_commit_msg` | `timber review commit-msg` in a `commit-msg` hook |

The Go builtins run at the `go.mod` workspace and need a Go toolchain.

Install the tools with mise:

```sh
mise use "github:nnutter/mdlint@latest"
mise use "go:github.com/alecthomas/go-check-sumtype/cmd/go-check-sumtype@latest"
mise use "go:github.com/kojah/gohawk@latest"
mise use "go:github.com/nnutter/constable/cmd/constable@latest"
mise use "go:github.com/securego/gosec/v2/cmd/gosec@latest"
mise use "go:github.com/nnutter/timber@latest"
mise use "go:github.com/nnutter/testifylint@0.0.0-20261101203540-577bf922d916"
mise use "go:golang.org/x/tools/cmd/goimports@latest"
mise use "go:go.uber.org/nilaway/cmd/nilaway@latest"
mise use go@latest
```

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

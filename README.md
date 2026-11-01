# hk-config

Extra [hk](https://hk.jdx.dev) builtins, published as a Pkl package so that any repository can import them.

hk ships a fixed set of builtins, and a config that amends hk's `Config.pkl` can only use those.
This package holds the builtins that hk does not ship.

## Use it

The package version is the hk version it targets, so replace `<hk-version>` below with the hk release you amend.
A release exists for each hk release, so pick the one that matches the hk version you run.

```pkl
// hk.pkl
amends "package://github.com/nnutter/hk-config/releases/download/v<hk-version>/hk-config@<hk-version>#/Config.pkl"

import "package://github.com/nnutter/hk-config/releases/download/v<hk-version>/hk-config@<hk-version>#/Builtins.pkl" as Extra

steps {
  ["mdlint"] = Extra.mdlint
}
```

This package's `Config.pkl` amends hk's, so your config and these builtins share one hk version.
Amending hk's `Config.pkl` directly also works, but then its version must equal the one this package targets, or the steps are different Pkl types and the config will not type-check.

## Builtins

| Name | Runs |
| --- | --- |
| `constable` | `constable ./...` to check, `constable -fix ./...` to fix, on `**/*.go` |
| `go_check_sumtype` | `go-check-sumtype -default-signifies-exhaustive=false -include-shared-interfaces ./...` on `**/*.go` |
| `gohawk` | `gohawk ./...` on `**/*.go` |
| `mdlint` | `mdlint format --check` and `mdlint check --no-fix` to check, `mdlint format` and `mdlint check --fix` to fix, on `**/*.md` and `**/*.markdown` |
| `nilaway` | `nilaway -include-pkgs $(go list -m) ./...` on `**/*.go` |
| `testifylint` | `testifylint ./...` to check, `testifylint -fix ./...` to fix, on `**/*.go` |
| `timber_commit_msg` | `timber review commit-msg` in a `commit-msg` hook |

The Go builtins run at the `go.mod` workspace and need a Go toolchain.

Install the tools with mise:

```sh
mise use "github:nnutter/mdlint@latest"
mise use "go:github.com/alecthomas/go-check-sumtype/cmd/go-check-sumtype@latest"
mise use "go:github.com/Antonboom/testifylint@latest"
mise use "go:github.com/kojah/gohawk@latest"
mise use "go:github.com/nnutter/constable/cmd/constable@latest"
mise use "go:github.com/nnutter/timber@latest"
mise use "go:go.uber.org/nilaway/cmd/nilaway@latest"
```

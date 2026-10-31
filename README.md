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
```

This package's `Config.pkl` amends hk's, so your config and these builtins share one hk version.
Amending hk's `Config.pkl` directly also works, but then its version must equal the one this package targets, or the steps are different Pkl types and the config will not type-check.

## Builtins

None yet.
Builtins come from `Builtins.pkl` in the same package and are assigned as steps.

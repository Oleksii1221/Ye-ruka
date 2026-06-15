# Project Governance

Ye-Ruka is maintained by Medvid Oleksii (Kico).

## Branches

- `master`: protected, stable, release-ready code;
- `dev`: integration branch for current development;
- `feature/*` and `fix/*`: short-lived focused branches.

## Releases

A release is prepared as a pull request from `dev` to `master`. After tests and manual checks pass, the version is updated, the pull request is merged, and a `vX.Y.Z` tag is created. GitHub Actions builds and publishes the Windows installer, portable ZIP, and checksums.

Emergency fixes branch from `master`, merge back into `master` through a pull request, and are then synchronized into `dev`.

## Decision making

The maintainer makes final decisions on product direction, safety constraints, supported hardware, releases, and repository access. Significant behavioral changes should be documented in an issue or pull request before release.

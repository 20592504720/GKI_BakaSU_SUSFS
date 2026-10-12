<div align="center">
# GKI BakaSU SUSFS
Building Android GKI kernels integrated with BakaSU and SUSFS via GitHub Actions.
[![Release](https://img.shields.io/github/v/release/coolzyd9107/GKI_BakaSU_SUSFS?label=Release&style=flat-square&logo=github&logoColor=white&color=2ea44f)](https://github.com/zhuzhuzihan/GKI_BakaSU_SUSFS/releases)
[![Build Kernel](https://github.com/zhuzhuzihan/GKI_BakaSU_SUSFS/actions/workflows/main.yml/badge.svg)](https://github.com/zhuzhuzihan/GKI_BakaSU_SUSFS/actions/workflows/main.yml)
[![Telegram](https://img.shields.io/static/v1?label=Telegram&message=Channel&color=0088cc)](https://t.me/BakaSUKernelBuilds)
[![BakaSU](https://img.shields.io/badge/KernelSU-BakaSU-5AA300?style=flat-square)](https://github.com/Baka-SU/BakaSU)
[![SUSFS](https://img.shields.io/badge/Filesystem-SUSFS-E67E22?style=flat-square)](https://gitlab.com/simonpunk/susfs4ksu)
</div>
## Overview
This repository provides cloud-based GitHub Actions workflows to generate AnyKernel3 flashable zip packages based on Android GKI KMIs and security patch levels. Regular builds integrate BakaSU with configurable optional features, while Clean builds are also supported to produce stock-like kernels without KernelSU, SUSFS, or optional patches.
Kernel versions and release revisions are loaded from JSON matrices under `data/android*/` and automatically updated by a scheduled data synchronization workflow.
## Important Notice
Due to recent major refactoring, build steps and resulting artifacts have expanded considerably. As a consequence, running the full build workflow across all kernel versions takes an excessively long time. Therefore, we will no longer run automated builds or publish full releases on a scheduled basis or upon major BakaSU updates. This decision aims to reduce the prolonged consumption of shared GitHub Actions compute resources. 
Users are encouraged to fork this repository and manually trigger single-kernel builds matching their specific kernel version, which substantially minimizes resource abuse. We apologize for any inconvenience caused. For detailed instructions on using the workflow in this repo and forks, please refer to the relevant sections below.
## Supported KMIs

| Android KMI | Kernel Branch | `build_target` Option |
| :--- | :--- | :--- |
| Android 12 | 5.10 | `android12-5.10` |
| Android 13 | 5.10 | `android13-5.10` |
| Android 13 | 5.15 | `android13-5.15` |
| Android 14 | 5.15 | `android14-5.15` |
| Android 14 | 6.1 | `android14-6.1` |
| Android 15 | 6.6 | `android15-6.6` |
| Android 16 | 6.12 | `android16-6.12` |
| Android 17 | 6.18 | `android17-6.18` |

Both 5.10 and 5.15 span multiple Android KMIs. Specifically, identical kernel version numbers exist across Android 13 and Android 14 on 5.15; thus, KMI cannot be determined solely by `5.15.xxx`. You must explicitly choose the corresponding Android version when targeting a specific release. Android 17 / 6.18 currently supports base compilation; certain auxiliary components will be skipped automatically depending on upstream status.
## Running Builds
1. Go to the [Actions](https://github.com/zhuzhuzihan/GKI_BakaSU_SUSFS/actions) tab, select the **Build Kernel** (构建内核) workflow, and click **Run workflow**.
2. Under `build_target`, select a target KMI, or choose `all` to build all targets. Note that `choice` is single-select; to compile multiple specific targets, trigger them individually.
3. Configure optional features and `release_type` as needed, then start the run.
4. Once completed, download build outputs from **Artifacts** on the run summary page, or from the Releases page if a Release was created.
### Filtering by Kernel Version
When `build_kernel_version` is enabled, version filtering takes precedence over default version selectors. `kernel_version_filter` accepts exact version strings or branch wildcards:

| Input | Description |
| :--- | :--- |
| `6.6.66` | Builds version `6.6.66` from the specified KMI matrix |
| `6.6.X` or `6.6.x` | Builds all 6.6 sub-versions within that KMI dataset |

Selection rules:
- 5.10: `kernel_android_version` must be set to `android12` or `android13`.
- 5.15: Must be set to `android13` or `android14`.
- 6.1, 6.6, 6.12, 6.18: Workflows automatically resolve to Android 14, 15, 16, and 17 KMIs, requiring no manual override.
Patch levels, release revisions, and LTS versions are retrieved directly from JSON datasets. Explicit version builds will not generate GitHub Releases, even if `release_type` is set to Pre-Release or Release.
### Release Types
The `release_type` option controls artifact publishing:
- `Actions`: Uploads outputs solely as GitHub Actions artifacts without creating a Release (Default).
- `Pre-Release`: Creates a pre-release upon successful completion (only on the upstream repository).
- `Release`: Creates a formal release upon successful completion (only on the upstream repository).
Forked repositories will only generate Actions artifacts and will not publish Releases upstream.
## BakaSU Branches
If `kernelsu_branch` is left empty, `main` is used by default. You may also specify a remote branch name or a full 40-character commit SHA. The workflow resolves and locks the commit SHA at startup so all KMIs in the same run share identical source code; release notes will link directly to the pinned BakaSU commit.
## Optional Build Features

| Option | Description |
| :--- | :--- |
| `clean_build` | Builds a clean kernel without BakaSU, SUSFS, or optional patches. |
| `cancel_susfs` | Disables SUSFS integration. Enabled by default; automatically skipped on Android 17 / 6.18 due to lack of upstream branches. |
| `use_zram` | Enables ZRAM enhancements (LZ4KD). Automatically skipped on Android 17 / 6.18 due to missing patches. |
| `use_bbg` | Applies the BBG anti-brick patch. |
| `use_rekernel` | Enables the Re-Kernel driver (experimental). Temporarily skipped on Android 17 / 6.18 pending adaptation to upstream source layout. |
| `cve_2026_43499_patch` | Applies the CVE-2026-43499 fix chain. Enabled by default; automatically skipped on 6.18 due to lack of adapted patches. |
| `build_bypass` | Builds an additional Bypass Image packaged alongside the standard Image. |
| `droidspaces` | Selects Droidspaces container patch slot: `off`, `678`, `123`, or `345`. 6.12+ uses upstream universal patches. |
| `droidspaces_ntsync` | Enables NTSync on supported combinations; requires Droidspaces. Automatically skipped on Android 17 / 6.18 due to missing patches. |
| `use_nomount` | Integrates kernel support for [NoMount](https://github.com/maxsteeel/nomount) mount meta-modules; requires companion NoMount module. Skipped on clean builds. |

Bypass mode is intended for diagnosing kernel module version compatibility issues, not for bypassing root detection. Enabling it initiates a second compilation pass, increasing total build time. During installation, select either the standard Image or Bypass Image according to installer prompts.
Droidspaces patches are experimental; different devices and kernel revisions may require experimenting with different patch slots. Android 16 / 6.12 and Android 17 / 6.18 only feature a single slot implementation, so selecting any non-`off` value works. Upstream lacks NTSync compatibility patches for Android 14 / 5.15; this combination will cause build failures and must remain disabled. Missing NTSync patches on Android 17 / 6.18 are automatically skipped.
## Build Artifacts
Artifact filenames include the Android KMI, full kernel version, and OS security patch level, appending upstream revisions when available. For example:
```text
android14-5.15.148-2024-05-r25-BakaSU-AnyKernel3.zip

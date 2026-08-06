# Development Guide

## 1. Environment

SaktiLinux AI is developed on Arch Linux. Currently we use the VirtualBox VM
`SaktiOS dev` (Arch, EFI, 4 GB RAM, 2 CPU, NAT port-forward `3022 -> 22`).

SSH into the VM:

```bash
ssh -p 3022 saktios@127.0.0.1
```

> If `sshd` isn't started yet, run inside the VM console:
> `sudo systemctl enable --now sshd`
> and set a password: `sudo passwd saktios`.

## 2. Repository

The repo currently lives on the Windows host inside the VirtualBox machine
folder (`E:\SaktiOS\SaktiOS dev`). For VM-based builds, clone/copy it into
the guest:

```bash
git clone /host/path saktilinux-ai
cd saktilinux-ai
```

## 3. Bootstrap the base system

```bash
sudo bash scripts/bootstrap-base.sh
```

This (idempotently) installs the manifests in `packages/lists/base.txt` and
configures the base systemd profile described in the script.

## 4. Install the desktop (Phase 2)

```bash
sudo bash scripts/install-desktop.sh
```

- Installs Plasma/Wayland, SDDM, Sakti plasmoids, themes, icons, fonts.
- Generates color schemes from `branding/colors.json`.
- Applies the user shell config (fonts, icons, default mode).

Switch work modes live:

```bash
sakti-modes switch developer   # or designer / cyber / default
sakti-modes list
sakti-modes current
```

## 5. Testing

```bash
bash tests/run-tests.sh
```

Requires Python 3 for the unit tests (`python3`). CI runs these on every
push/PR — see `.github/workflows/ci.yml`.

## 6. Phase workflow

1. Work only in the current phase scope.
2. Never touch unrelated files; never overwrite working code.
3. Documentation, tests, changelog, and a commit accompany each phase.
4. After the phase is complete we **stop** for confirmation.
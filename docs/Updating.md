# Updating INKBIRD BBQ from Git

Until INKBIRD BBQ for Home Assistant is distributed through HACS, the recommended development installation/update method is the supplied updater script.

Once HACS becomes the normal distribution path, regular users should use HACS for installation and updates. The script can remain useful for development branches, pre-releases and protocol testing.

## What the updater does

The updater:

1. clones the repository automatically when no local clone exists;
2. fetches release tags and remote branches;
3. shows an interactive version menu when no ref is supplied;
4. exports only `custom_components/inkbird_bbq` from the selected Git commit;
5. validates the expected integration structure and manifest;
6. backs up the currently installed integration;
7. installs the selected version;
8. runs `ha core check`;
9. automatically restores the previous integration if validation fails;
10. asks before restarting Home Assistant.

The updater never restarts Home Assistant after a failed validation.

## Recommended layout

```text
/config/ha-inkbird-bbq/
/config/custom_components/inkbird_bbq/
/config/update_inkbird_bbq.sh
/config/.inkbird_bbq_backups/
```

## First installation of the updater

Copy `scripts/update_inkbird_bbq.sh` from this repository to:

```text
/config/update_inkbird_bbq.sh
```

Then make it executable:

```bash
chmod +x /config/update_inkbird_bbq.sh
```

The repository itself does not need to be cloned manually. The updater will clone it to `/config/ha-inkbird-bbq` when required.

## Interactive update

Run:

```bash
/config/update_inkbird_bbq.sh
```

The menu lists recent release tags first, followed by remote branches. During development this allows switching between a stable/release tag and a development branch without manually copying files.

## Install a specific branch or tag

For example:

```bash
/config/update_inkbird_bbq.sh feature/initial-integration-skeleton
```

Later, when release tags exist:

```bash
/config/update_inkbird_bbq.sh v0.1.0
```

## Non-interactive restart

For development use, a successful validation can automatically restart Home Assistant:

```bash
/config/update_inkbird_bbq.sh --yes feature/initial-integration-skeleton
```

Without `--yes`, the script asks before restarting.

## Validation and rollback

Before installation, the updater verifies that the selected Git revision contains the expected integration path and required files.

After copying the integration, it runs:

```bash
ha core check
```

If the check fails:

- the newly installed integration is removed;
- the previous copy is restored from `/config/.inkbird_bbq_backups/`;
- Home Assistant is not restarted.

The backup directory is timestamped so previous test versions remain available for manual recovery.

## Installed revision metadata

The updater writes:

```text
/config/custom_components/inkbird_bbq/.installed_revision
/config/custom_components/inkbird_bbq/.installed_ref
```

These make it easy to determine exactly which Git commit/ref is installed during development and troubleshooting.

## Relationship with HACS

This updater is intentionally a temporary/development mechanism.

The target long-term user experience is:

```text
HACS -> INKBIRD BBQ -> Download / Update
```

When the integration is ready for normal HACS distribution, the README and installation documentation will make HACS the default path. The Git updater may remain documented only for developers, beta testers and branch testing.

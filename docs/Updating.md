# Updating INKBIRD BBQ

## Recommended method: HACS

HACS is now the preferred installation and update path for normal Home Assistant testing.

The repository passes the official HACS Validation workflow. Until a stable tagged release is published, add the repository to HACS as a custom **Integration** repository:

\`https://github.com/bjedelijn/ha-inkbird-bbq\`

Then install or update **INKBIRD BBQ** from HACS and restart Home Assistant when requested.

At the current pre-release stage HACS follows the development version on \`main\`. Stable version tags/releases will be introduced later.

## Development updater

The included updater remains useful when testing a feature branch, protocol experiment, older revision or explicit Git ref.

Script:

\`scripts/update_inkbird_bbq.sh\`

It:

1. clones the repository automatically when no local clone exists;
2. fetches release tags and remote branches;
3. shows an interactive version menu when no ref is supplied;
4. exports only \`custom_components/inkbird_bbq\` from the selected Git commit;
5. validates the expected integration structure and manifest;
6. backs up the currently installed integration;
7. installs the selected version;
8. runs \`ha core check\`;
9. restores the previous integration automatically if validation fails;
10. asks before restarting Home Assistant.

The updater never restarts Home Assistant after a failed validation.

## Recommended development layout

\`\`\`text
/config/ha-inkbird-bbq/
/config/custom_components/inkbird_bbq/
/config/update_inkbird_bbq.sh
/config/.inkbird_bbq_backups/
\`\`\`

## First installation of the updater

Copy \`scripts/update_inkbird_bbq.sh\` to:

\`\`\`text
/config/update_inkbird_bbq.sh
\`\`\`

Then make it executable:

\`\`\`bash
chmod +x /config/update_inkbird_bbq.sh
\`\`\`

The updater clones the repository to \`/config/ha-inkbird-bbq\` when required.

## Interactive update

\`\`\`bash
/config/update_inkbird_bbq.sh
\`\`\`

## Install a specific branch or tag

Examples:

\`\`\`bash
/config/update_inkbird_bbq.sh main
/config/update_inkbird_bbq.sh docs/refresh-dev3
\`\`\`

When release tags exist:

\`\`\`bash
/config/update_inkbird_bbq.sh v0.1.0
\`\`\`

## Non-interactive restart

\`\`\`bash
/config/update_inkbird_bbq.sh --yes main
\`\`\`

Without \`--yes\`, the script asks before restarting.

## Validation and rollback

After copying the integration, the updater runs:

\`\`\`bash
ha core check
\`\`\`

If the check fails, the newly installed copy is removed, the previous copy is restored from \`/config/.inkbird_bbq_backups/\`, and Home Assistant is not restarted.

## Installed revision metadata

The updater writes:

\`\`\`text
/config/custom_components/inkbird_bbq/.installed_revision
/config/custom_components/inkbird_bbq/.installed_ref
\`\`\`

Use these files when debugging which exact Git revision is installed.

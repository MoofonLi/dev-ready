# Configure email sending and error reporting

The **Email sending** and **Error reporting** sections can run separately or
together on any invocation of `setup-project`. Neither depends on whether this
is the project's first setup.

Read `.env` and report the current `SMTP_HOST`, `SMTP_USER`,
`EMAILS_FROM_EMAIL`, and whether `SMTP_PASSWORD` and `SENTRY_DSN` are set. Never
print a stored password.
Optional entries absent from `.env` are unset; add them only when configuring
the corresponding section.

For whichever of the two sections the user selected, ask one shared gate
question: "Configure the selected email and error-reporting sections now?" The
default is No. If the user declines, stop without asking anything else or
changing `.env`.

If the user accepts, ask only for the values belonging to the selected sections.

For **Email sending**, ask for these four values:

1. `SMTP_HOST` — the provider's SMTP host.
2. `SMTP_USER` — the provider's SMTP user.
3. `SMTP_PASSWORD` — before asking, say in the same message: "An SMTP password
   typed here enters this conversation and its stored transcript, which can
   have a different retention policy from this project's disk. Prefer a
   provider app password over an account password. Leave this blank to set
   `SMTP_PASSWORD` directly in `.env` instead."
4. `EMAILS_FROM_EMAIL` — the address messages should come from.

For **Error reporting**, ask for one value:

1. `SENTRY_DSN` — the error-reporting DSN.

When both sections are selected, the one accepted gate therefore asks exactly
five values. Selecting Email sending alone never walks through Error reporting,
and selecting Error reporting alone never asks for SMTP values.

Write the supplied values to `.env`, preserving unrelated entries. If the SMTP
password was blank, preserve its current value and remind the user to edit that
one entry by hand. Never echo a supplied or stored password.

The generated `.env` uses local email-capture settings: `SMTP_PORT=1025` and
`SMTP_TLS=False`; the backend defaults to `SMTP_SSL=False` when that entry is
absent. Leave these settings unchanged when using the local capture service.

For a backend running directly on the host, configure an external provider
using its documented transport settings. A STARTTLS provider commonly needs
`SMTP_PORT=587`, `SMTP_TLS=True`, and `SMTP_SSL=False`; implicit TLS needs the
provider's SSL port and TLS/SSL values instead. Update or add all three `.env`
entries together; do not reuse the local capture port for an external provider.

Base Compose does not forward these three transport settings. For a container
deployment, they must also be mapped into the backend environment, shared
with `prestart`, before recreating the services. An `.env` edit alone does not
configure container transport. Leave deployment changes to the deployment
step; point to `deployment.md` and explain the required mappings, for example:

```yaml
SMTP_PORT: ${SMTP_PORT:-587}
SMTP_TLS: ${SMTP_TLS:-true}
SMTP_SSL: ${SMTP_SSL:-false}
```

Local Compose captures email with Mailcatcher: `compose.override.yml`
overrides the SMTP host, port, and TLS settings. Changing `.env` alone does
not switch that local Compose service to an external provider. Deployment
configuration belongs in `deployment.md`.

Email and error-reporting changes take effect after an application restart.
Recreate Compose services when changing their environment.

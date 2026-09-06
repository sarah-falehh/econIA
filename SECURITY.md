# Security policy

## Supported version

Security fixes target the latest release on the `main` branch.

## Reporting a vulnerability

Do not open a public issue containing credentials, private economic documents, personal information or an exploitable vulnerability. Contact the repository owner privately through the contact method listed on the GitHub profile.

Include the affected version, reproduction steps, potential impact and any safe mitigation you identified.

## Deployment notes

- Change the local bootstrap administrator credential before shared deployment.
- Never commit `.streamlit/secrets.toml`, local SQLite databases, uploaded reports or generated exports.
- Place the application behind HTTPS and appropriate network access controls.
- Review user roles and audit logs regularly.
- Treat source documents and extracted evidence as potentially confidential.

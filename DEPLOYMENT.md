# Production deployment

The production server deploys every new fast-forward commit pushed to `main`.
The server-side `oldsupra-deploy.timer` polls GitHub approximately once per
minute and runs `/usr/local/sbin/oldsupra-deploy` when the remote revision
changes.

Each deployment:

1. fetches `origin/main` with the repository-scoped deploy key;
2. rejects force-pushed/non-fast-forward history and tracked credential files;
3. checks Python syntax, dependencies, Django configuration, and migrations in
   a temporary worktree;
4. creates and verifies a transaction-safe SQLite backup;
5. installs pinned dependencies, applies migrations, and collects static files;
6. restarts `oldsupra.service`; and
7. records the revision only after local HTTP health verification succeeds.

If a step after the service is stopped fails, the deployer restores the prior
commit and database backup, rebuilds static files, and restarts the previous
version. The latest ten pre-deployment database backups are retained in the
server's protected backup directory.

## Operations

Check the timer and latest deployment:

```bash
systemctl status oldsupra-deploy.timer
journalctl -u oldsupra-deploy.service -n 100 --no-pager
cat /var/lib/oldsupra-deploy/deployed-revision
```

Run the same guarded deployment immediately:

```bash
systemctl start oldsupra-deploy.service
```

Never commit `.env`, `.secret_key`, the SQLite database, uploaded media, logs,
or deploy-key material.

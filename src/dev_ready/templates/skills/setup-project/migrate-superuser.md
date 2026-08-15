# Migrate the superuser without resetting data

This route preserves the database. Explain the sequence and let the user run
each operation; do not execute it from `setup-project`.

1. Back up the database and start the application with its current `.env`.
2. Through the backend's supported database session and user model, create the
   new email address as an active superuser with a new password.
3. Confirm that the new account can authenticate and has superuser access.
4. Change `FIRST_SUPERUSER` in `.env` to the new account's email.
5. Delete the old superuser row only after the new account is verified. Keep any
   application records that refer to it consistent with the project's data
   model.
6. Replace `FIRST_SUPERUSER_PASSWORD` in `.env` with a fresh random value that
   is not used by either account. Once the configured email already exists, the
   startup initializer skips creation and this value is only a safe unused
   fallback.
7. Restart the application and verify the new login again.

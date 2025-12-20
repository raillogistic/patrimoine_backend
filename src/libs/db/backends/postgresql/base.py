from django.db.backends.postgresql.base import (
    DatabaseWrapper as PostgresDatabaseWrapper,
)


class DatabaseWrapper(PostgresDatabaseWrapper):
    def chunked_cursor(self):
        # Avoid server-side cursors (e.g., PgBouncer transaction pooling).
        return self.cursor()

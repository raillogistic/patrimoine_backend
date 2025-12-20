import os
import subprocess

from django.conf import settings
from django.http import HttpResponse


def download_database_sql(request):
    """
    Export the database schema and data to a .sql file and return it as a downloadable response.
    """
    # Define the file path
    output_file = os.path.join(settings.BASE_DIR, "db_backup.sql")

    try:
        # Get database settings
        db_settings = settings.DATABASES["default"]
        db_name = db_settings["NAME"]
        db_user = db_settings["USER"]
        db_password = db_settings["PASSWORD"]
        db_host = db_settings.get("HOST", "localhost")
        db_port = db_settings.get("PORT", "")

        # Check if the database engine is supported
        if "mysql" in db_settings["ENGINE"]:
            # MySQL/MariaDB dump command
            command = f"mysqldump --user={db_user} --password={db_password} --host={db_host} --port={db_port} {db_name} > {output_file}"
        elif "postgresql" in db_settings["ENGINE"]:
            # PostgreSQL dump command
            os.environ["PGPASSWORD"] = db_password
            command = f"pg_dump --username={db_user} --host={db_host} --port={db_port} --format=plain --no-owner --file={output_file} {db_name}"
        else:
            return HttpResponse("Unsupported database engine", status=400)

        # Execute the command
        subprocess.run(command, shell=True, check=True)

        # Read the file and prepare the response
        with open(output_file, "rb") as f:
            response = HttpResponse(f.read(), content_type="application/sql")
            response["Content-Disposition"] = f'attachment; filename="db_backup.sql"'
            return response
    except Exception as e:
        return HttpResponse(f"Error during database export: {e}", status=500)
    finally:
        # Clean up the file if it exists
        if os.path.exists(output_file):
            os.remove(output_file)

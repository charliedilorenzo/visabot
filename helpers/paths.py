from pathlib import Path

BASE_PATH = Path(__file__).parent.parent
DATABASE_PATH = BASE_PATH / "database" / "database.db"
SCHEMA_PATH = BASE_PATH / "database" / "schema.sql"
MEDIA_PATH = BASE_PATH / "media"
LOG_PATH = BASE_PATH / ".logs"

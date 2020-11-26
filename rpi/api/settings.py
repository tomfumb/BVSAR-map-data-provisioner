import os


API_LOG_DIR = os.environ.get(
    "API_LOG_DIR", os.path.join(os.path.sep, "www", "api", "log")
)
UPLOADS_DIR = os.environ.get("UPLOADS_DIR", os.path.join(os.path.sep, "www", "uploads"))
UPLOADS_PATH = "/uploads/files"
TILES_DIR = os.environ.get("TILES_DIR", os.path.join(os.path.sep, "www", "tiles"))
TILES_PATH = "/tiles/files"
FILES_DIR = os.environ.get("FILES_DIR", os.path.join(os.path.sep, "www", "files"))
FILES_PATH = "/files/files"
UI_DIR = os.environ.get("UI_DIR", os.path.join(os.path.sep, "www", "web"))
UI_PATH = "/web"
PDF_EXPORT_MAX_TILES = int(os.environ.get("PDF_EXPORT_MAX_TILES", 1024))
CURRENT_DIR = os.path.dirname(__file__)
PARENT_TEMP_DIR = os.path.join(CURRENT_DIR, "export", "temp")

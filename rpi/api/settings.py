import os


UPLOADS_DIR = os.environ.get("UPLOADS_DIR", os.path.join(os.path.sep, "www", "uploads"))
UPLOADS_PATH = "/uploads/files"
TILES_DIR = os.environ.get("TILES_DIR", os.path.join(os.path.sep, "www", "tiles"))
TILES_PATH = "/tiles/files"
UI_DIR = os.environ.get("UI_DIR", os.path.join(os.path.sep, "www", "web"))
UI_PATH = "/web"
PDF_EXPORT_MAX_PX = int(os.environ.get("PDF_EXPORT_MAX_PX", 500000000))
CURRENT_DIR = os.path.dirname(__file__)
PARENT_TEMP_DIR = os.path.join(CURRENT_DIR, "export", "temp")

import os

overwrite_existing = int(os.environ.get("OVERWRITE_EXISTING", 0)) == 0

def skip_file_creation(path: str) -> bool:
    return os.path.exists(path) and overwrite_existing

def remove_intermediaries() -> bool:
    return int(os.environ.get("REMOVE_INTERMEDIARIES", 1)) == 1
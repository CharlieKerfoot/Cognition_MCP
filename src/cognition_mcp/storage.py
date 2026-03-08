import json
from datetime import datetime, timezone
from pathlib import Path

CACHE_DIR = Path.home() / '.cognition_mcp'
LIBRARY_FILE = CACHE_DIR / 'library.json'

_EMPTY: dict = {
	'books': [],
	'films': [],
	'notes': [],
	'meta': {
		'goodreads_username': None,
		'letterboxd_username': None,
		'obsidian_vault': None,
		'last_synced': None,
	},
}


def load() -> dict:
	if not LIBRARY_FILE.exists():
		return {**_EMPTY, 'books': [], 'films': [], 'notes': [], 'meta': dict(_EMPTY['meta'])}
	with LIBRARY_FILE.open() as f:
		data = json.load(f)
	data.setdefault('notes', [])
	data['meta'].setdefault('obsidian_vault', None)
	return data


def save(library: dict) -> None:
	CACHE_DIR.mkdir(parents=True, exist_ok=True)
	library['meta']['last_synced'] = datetime.now(timezone.utc).isoformat()
	with LIBRARY_FILE.open('w') as f:
		json.dump(library, f, indent=2)

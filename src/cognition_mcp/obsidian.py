import re
from datetime import datetime, timezone
from pathlib import Path


def scan_vault(vault_path: str) -> list[dict]:
	root = Path(vault_path).expanduser()
	if not root.exists():
		raise ValueError(f'Vault path not found: {vault_path}')
	if not root.is_dir():
		raise ValueError(f'Not a directory: {vault_path}')

	notes = []
	for path in sorted(root.rglob('*.md')):
		if any(part.startswith('.') for part in path.parts):
			continue
		try:
			content = path.read_text(encoding='utf-8')
			notes.append(_parse_note(path, content, root))
		except (OSError, UnicodeDecodeError):
			continue
	return notes


def _parse_note(path: Path, content: str, root: Path) -> dict:
	frontmatter, body = _split_frontmatter(content)
	return {
		'title': path.stem,
		'path': str(path.relative_to(root)),
		'tags': _extract_tags(frontmatter, body),
		'modified': datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).date().isoformat(),
		'content': body.strip(),
	}


def _split_frontmatter(content: str) -> tuple[str, str]:
	if content.startswith('---'):
		end = content.find('\n---', 3)
		if end != -1:
			return content[3:end], content[end + 4:]
	return '', content


def _extract_tags(frontmatter: str, body: str) -> list[str]:
	tags: set[str] = set()

	inline = re.search(r'^tags:\s*\[([^\]]*)\]', frontmatter, re.MULTILINE)
	if inline:
		tags.update(t.strip().strip('"\'') for t in inline.group(1).split(',') if t.strip())
	else:
		block = re.search(r'^tags:\s*\n((?:[ \t]+-[ \t]+.+\n?)+)', frontmatter, re.MULTILINE)
		if block:
			tags.update(re.findall(r'- (.+)', block.group(1)))
		else:
			single = re.search(r'^tags:\s*(\S.*)', frontmatter, re.MULTILINE)
			if single:
				tags.add(single.group(1).strip('"\''))

	tags.update(re.findall(r'(?<![&\w])#([A-Za-z][A-Za-z0-9/_-]*)', body))
	return sorted(tags)

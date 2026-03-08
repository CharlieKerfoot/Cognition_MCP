import json

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from cognition_mcp import goodreads, letterboxd, news, obsidian, storage

load_dotenv()

mcp = FastMCP('Cognition')


@mcp.tool()
async def connect_goodreads(profile_url_or_id: str) -> str:
	"""Connect to a Goodreads account and load all books from the "read" shelf.

	Args:
		profile_url_or_id: The Goodreads profile URL or numeric user ID.
			URL example: https://www.goodreads.com/review/list/167725774-your-name
			ID example: 167725774
	"""
	try:
		books = await goodreads.fetch_read_shelf(profile_url_or_id)
	except ValueError as e:
		return str(e)
	except Exception as e:
		return f'Failed to fetch Goodreads data: {e}'

	library = storage.load()
	library['books'] = books
	library['meta']['goodreads_username'] = profile_url_or_id
	storage.save(library)
	return f'Loaded {len(books)} books from Goodreads.'


@mcp.tool()
async def connect_letterboxd(username: str) -> str:
	"""Connect to a Letterboxd account and load recent diary entries via RSS.
	Note: RSS only includes recent activity (~50 entries). For your complete history,
	use import_letterboxd_csv after exporting your data from Letterboxd settings.

	Args:
		username: The Letterboxd username (from your profile URL, e.g. "johndoe")
	"""
	try:
		films = await letterboxd.fetch_diary_rss(username)
	except Exception as e:
		return f'Failed to fetch Letterboxd RSS: {e}'

	library = storage.load()
	library['films'] = letterboxd.merge_films(library['films'], films)
	library['meta']['letterboxd_username'] = username
	storage.save(library)
	return (
		f'Loaded {len(films)} recent films from Letterboxd for @{username}. '
		'For your full watch history, use import_letterboxd_csv with your exported diary.csv.'
	)


@mcp.tool()
async def import_letterboxd_csv(csv_content: str) -> str:
	"""Import complete Letterboxd watch history from the raw text content of an exported diary.csv file.
	The user should upload or paste their diary.csv — pass the full file contents as csv_content.
	Export instructions: Letterboxd → Settings → Import & Export → Export Your Data → unzip → diary.csv.

	Args:
		csv_content: The full text content of the diary.csv file
	"""
	try:
		films = letterboxd.parse_diary_csv(csv_content)
	except Exception as e:
		return f'Failed to parse CSV: {e}'

	library = storage.load()
	before = len(library['films'])
	library['films'] = letterboxd.merge_films(library['films'], films)
	added = len(library['films']) - before
	storage.save(library)
	return f'Imported {len(films)} entries from CSV. Added {added} new films (skipped {len(films) - added} duplicates). Total: {len(library["films"])} films.'


@mcp.tool()
async def connect_obsidian(vault_path: str) -> str:
	"""Connect an Obsidian vault and load all notes for use in idea and current events exploration.

	Args:
		vault_path: Absolute path to the Obsidian vault directory (e.g. "/Users/you/Documents/MyVault")
	"""
	try:
		notes = obsidian.scan_vault(vault_path)
	except ValueError as e:
		return str(e)
	except Exception as e:
		return f'Failed to scan vault: {e}'

	library = storage.load()
	library['notes'] = notes
	library['meta']['obsidian_vault'] = vault_path
	storage.save(library)
	return f'Loaded {len(notes)} notes from Obsidian vault at {vault_path}.'


@mcp.tool()
async def get_media_library() -> str:
	"""Return a summary of all books, films, and notes in your library."""
	library = storage.load()
	books = library['books']
	films = library['films']
	notes = library['notes']
	meta = library['meta']

	if not books and not films and not notes:
		return (
			'Your library is empty. '
			'Use connect_goodreads, connect_letterboxd (or import_letterboxd_csv), '
			'and connect_obsidian to get started.'
		)

	book_ratings = [b['rating'] for b in books if b.get('rating')]
	film_ratings = [f['rating'] for f in films if f.get('rating')]
	book_dates = sorted(b['date_read'] for b in books if b.get('date_read'))
	film_dates = sorted(f['watch_date'] for f in films if f.get('watch_date'))
	note_dates = sorted(n['modified'] for n in notes if n.get('modified'))

	summary = {
		'books': {
			'count': len(books),
			'avg_rating': round(sum(book_ratings) / len(book_ratings), 2) if book_ratings else None,
			'date_range': [book_dates[0], book_dates[-1]] if book_dates else None,
			'goodreads_username': meta.get('goodreads_username'),
		},
		'films': {
			'count': len(films),
			'avg_rating': round(sum(film_ratings) / len(film_ratings), 2) if film_ratings else None,
			'date_range': [film_dates[0], film_dates[-1]] if film_dates else None,
			'letterboxd_username': meta.get('letterboxd_username'),
		},
		'notes': {
			'count': len(notes),
			'date_range': [note_dates[0], note_dates[-1]] if note_dates else None,
			'obsidian_vault': meta.get('obsidian_vault'),
		},
		'last_synced': meta.get('last_synced'),
	}
	return json.dumps(summary, indent=2)


@mcp.tool()
async def explore_idea(idea: str) -> str:
	"""Return your full media library so you can explore how a personal idea connects
	to the books and films you've consumed. Describe any idea, question, or theme you've
	been thinking about and this tool will surface your full reading and viewing history
	for analysis.

	Args:
		idea: Any idea, question, or theme you want to explore (e.g. "the tension between
		      freedom and belonging" or "why do systems resist change even when it's needed?")
	"""
	library = storage.load()
	books = library['books']
	films = library['films']
	notes = library['notes']

	if not books and not films and not notes:
		return (
			'Your library is empty. '
			'Connect your Goodreads, Letterboxd, and Obsidian accounts first.'
		)

	books, films, notes = _slim_library(books, films, notes)
	return json.dumps(
		{
			'idea': idea,
			'instruction': (
				'Using the books, films, and personal notes below, identify the most surprising and specific '
				'connections to this idea. Go beyond surface-level matches — find thematic echoes, '
				'contrasting perspectives, or works that reframe the idea in an unexpected way. '
				'Where relevant, draw on the user\'s own notes to show how their thinking relates to or '
				'diverges from what they have read and watched. Reference actual titles and quote reviews '
				'or note content where available.'
			),
			'books': books,
			'films': films,
			'notes': notes,
		},
		indent=2,
	)


@mcp.tool()
async def explore_current_events(topic: str) -> str:
	"""Fetch recent news on a topic and return it alongside your media library so you
	can explore how current events connect to books and films you've consumed.

	Args:
		topic: A current event, trend, or news topic to explore (e.g. "AI regulation",
		       "housing crisis", "loneliness epidemic")
	"""
	library = storage.load()
	books = library['books']
	films = library['films']
	notes = library['notes']

	if not books and not films and not notes:
		return (
			'Your library is empty. '
			'Connect your Goodreads, Letterboxd, and Obsidian accounts first.'
		)

	try:
		articles = await news.fetch_articles(topic)
	except RuntimeError as e:
		return str(e)
	except Exception as e:
		return f'Failed to fetch news: {e}'

	books, films, notes = _slim_library(books, films, notes)
	return json.dumps(
		{
			'topic': topic,
			'instruction': (
				'Using the news articles, media library, and personal notes below, find the most '
				'illuminating connections — historical parallels, fictional prophecies, philosophical '
				'frameworks, or contrarian takes that the user\'s consumed media and their own thinking '
				'offers on this current event. Be specific: name titles, cite plot points or arguments, '
				'reference note content, and construct a genuinely novel insight that the user is '
				'unlikely to have made themselves.'
			),
			'news_articles': articles,
			'books': books,
			'films': films,
			'notes': notes,
		},
		indent=2,
	)


def _trim(text: str | None, limit: int) -> str:
	if not text:
		return ''
	return text if len(text) <= limit else text[:limit] + '…'


def _slim_library(books: list, films: list, notes: list) -> tuple[list, list, list]:
	slim_books = [
		{**b, 'description': _trim(b.get('description'), 200), 'review': _trim(b.get('review'), 300)}
		for b in books
	]
	slim_notes = [
		{**n, 'content': _trim(n.get('content'), 600)}
		for n in notes
	]
	return slim_books, films, slim_notes


def main() -> None:
	mcp.run(transport='stdio')

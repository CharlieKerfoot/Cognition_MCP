import json
from pathlib import Path

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from cognition_mcp import goodreads, letterboxd, news, storage

load_dotenv()

mcp = FastMCP('Cognition')


@mcp.tool()
async def connect_goodreads(username: str) -> str:
	"""Connect to a Goodreads account and load all books from the "read" shelf.

	Args:
		username: The Goodreads username (from your profile URL, e.g. "johndoe")
	"""
	try:
		books = await goodreads.fetch_read_shelf(username)
	except ValueError as e:
		return str(e)
	except Exception as e:
		return f'Failed to fetch Goodreads data: {e}'

	library = storage.load()
	library['books'] = books
	library['meta']['goodreads_username'] = username
	storage.save(library)
	return f'Loaded {len(books)} books from Goodreads for @{username}.'


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
async def import_letterboxd_csv(file_path: str) -> str:
	"""Import complete Letterboxd watch history from an exported CSV file.
	Export your data at: Letterboxd → Settings → Import & Export → Export Your Data.
	Unzip the downloaded file and point this tool at diary.csv.

	Args:
		file_path: Absolute path to the diary.csv file from your Letterboxd export
	"""
	path = Path(file_path).expanduser()
	if not path.exists():
		return f'File not found: {file_path}'

	try:
		content = path.read_text(encoding='utf-8')
		films = letterboxd.parse_diary_csv(content)
	except Exception as e:
		return f'Failed to parse CSV: {e}'

	library = storage.load()
	before = len(library['films'])
	library['films'] = letterboxd.merge_films(library['films'], films)
	added = len(library['films']) - before
	storage.save(library)
	return f'Imported {len(films)} entries from CSV. Added {added} new films (skipped {len(films) - added} duplicates). Total: {len(library["films"])} films.'


@mcp.tool()
async def get_media_library() -> str:
	"""Return a summary of all books and films in your media library."""
	library = storage.load()
	books = library['books']
	films = library['films']
	meta = library['meta']

	if not books and not films:
		return (
			'Your media library is empty. '
			'Use connect_goodreads and connect_letterboxd (or import_letterboxd_csv) to get started.'
		)

	book_ratings = [b['rating'] for b in books if b.get('rating')]
	film_ratings = [f['rating'] for f in films if f.get('rating')]

	book_dates = sorted(b['date_read'] for b in books if b.get('date_read'))
	film_dates = sorted(f['watch_date'] for f in films if f.get('watch_date'))

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

	if not books and not films:
		return (
			'Your media library is empty. '
			'Connect your Goodreads and Letterboxd accounts first.'
		)

	return json.dumps(
		{
			'idea': idea,
			'instruction': (
				'Using the books and films below, identify the most surprising and specific '
				'connections to this idea. Go beyond surface-level matches — find thematic echoes, '
				'contrasting perspectives, or works that reframe the idea in an unexpected way. '
				'Reference actual titles and quote reviews where available.'
			),
			'books': books,
			'films': films,
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

	if not books and not films:
		return (
			'Your media library is empty. '
			'Connect your Goodreads and Letterboxd accounts first.'
		)

	try:
		articles = await news.fetch_articles(topic)
	except RuntimeError as e:
		return str(e)
	except Exception as e:
		return f'Failed to fetch news: {e}'

	return json.dumps(
		{
			'topic': topic,
			'instruction': (
				'Using the news articles and the media library below, find the most illuminating '
				'connections — historical parallels, fictional prophecies, philosophical frameworks, '
				'or contrarian takes that the user\'s consumed media offers on this current event. '
				'Be specific: name titles, cite plot points or arguments, and construct a genuinely '
				'novel insight that the user is unlikely to have made themselves.'
			),
			'news_articles': articles,
			'books': books,
			'films': films,
		},
		indent=2,
	)


def main() -> None:
	mcp.run(transport='stdio')

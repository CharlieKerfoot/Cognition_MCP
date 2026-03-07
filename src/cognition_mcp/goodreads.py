import re

import feedparser
import httpx


async def resolve_user_id(username: str) -> str:
	async with httpx.AsyncClient(follow_redirects=True) as client:
		response = await client.get(
			f'https://www.goodreads.com/{username}',
			headers={'User-Agent': 'Mozilla/5.0'},
		)
	match = re.search(r'/user/show/(\d+)', str(response.url))
	if not match:
		raise ValueError(
			f'Could not resolve Goodreads user ID for "{username}". '
			'Make sure your profile is public and the username is correct.'
		)
	return match.group(1)


async def fetch_read_shelf(username: str) -> list[dict]:
	user_id = await resolve_user_id(username)
	url = f'https://www.goodreads.com/review/list_rss/{user_id}?shelf=read'
	async with httpx.AsyncClient() as client:
		response = await client.get(url, headers={'User-Agent': 'Mozilla/5.0'})
		response.raise_for_status()

	feed = feedparser.parse(response.text)
	books = []
	for entry in feed.entries:
		books.append(
			{
				'title': entry.get('title', ''),
				'author': entry.get('author_name', ''),
				'rating': _parse_int(entry.get('user_rating')),
				'review': entry.get('user_review', '') or '',
				'date_read': entry.get('user_read_at', '') or '',
				'description': _strip_html(entry.get('book_description', '') or ''),
				'year_published': _parse_int(entry.get('book_published')),
				'num_pages': _parse_int(entry.get('num_pages')),
			}
		)
	return books


def _parse_int(value) -> int | None:
	try:
		return int(value)
	except (TypeError, ValueError):
		return None


def _strip_html(text: str) -> str:
	return re.sub(r'<[^>]+>', '', text).strip()

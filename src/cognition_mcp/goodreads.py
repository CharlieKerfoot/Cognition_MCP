import re

import feedparser
import httpx


def extract_user_id(url_or_id: str) -> str:
	stripped = url_or_id.strip()
	if re.fullmatch(r'\d+', stripped):
		return stripped
	match = re.search(r'/(?:review/list|user/show)/(\d+)', stripped)
	if not match:
		raise ValueError(
			f'Could not find a Goodreads user ID in "{url_or_id}". '
			'Pass your profile URL (e.g. https://www.goodreads.com/review/list/167725774-your-name) '
			'or just the numeric ID.'
		)
	return match.group(1)


async def fetch_read_shelf(url_or_id: str) -> list[dict]:
	user_id = extract_user_id(url_or_id)
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

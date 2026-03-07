import csv
import io

import feedparser
import httpx


async def fetch_diary_rss(username: str) -> list[dict]:
	url = f'https://letterboxd.com/{username}/rss/'
	async with httpx.AsyncClient() as client:
		response = await client.get(url, headers={'User-Agent': 'Mozilla/5.0'})
		response.raise_for_status()

	feed = feedparser.parse(response.text)
	films = []
	for entry in feed.entries:
		film_title = entry.get('letterboxd_filmtitle') or entry.get('title', '')
		watch_date = entry.get('letterboxd_watcheddate', '')
		rating_raw = entry.get('letterboxd_memberrating')
		rewatch = entry.get('letterboxd_rewatch', 'No').lower() == 'yes'
		liked = entry.get('letterboxd_memberlike', 'No').lower() == 'yes'
		year_raw = entry.get('letterboxd_filmyear')

		if not watch_date:
			continue

		films.append(
			{
				'title': film_title,
				'year': _parse_int(year_raw),
				'rating': _parse_float(rating_raw),
				'watch_date': watch_date,
				'rewatched': rewatch,
				'liked': liked,
			}
		)
	return films


def parse_diary_csv(content: str) -> list[dict]:
	reader = csv.DictReader(io.StringIO(content))
	films = []
	for row in reader:
		films.append(
			{
				'title': row.get('Name', ''),
				'year': _parse_int(row.get('Year')),
				'rating': _parse_float(row.get('Rating')),
				'watch_date': row.get('Watched Date', '') or row.get('Date', ''),
				'rewatched': row.get('Rewatch', '').strip().lower() == 'yes',
				'liked': False,
			}
		)
	return [f for f in films if f['title']]


def merge_films(existing: list[dict], incoming: list[dict]) -> list[dict]:
	seen = {(f['title'], f.get('year'), f.get('watch_date')) for f in existing}
	merged = list(existing)
	for film in incoming:
		key = (film['title'], film.get('year'), film.get('watch_date'))
		if key not in seen:
			merged.append(film)
			seen.add(key)
	return merged


def _parse_int(value) -> int | None:
	try:
		return int(value)
	except (TypeError, ValueError):
		return None


def _parse_float(value) -> float | None:
	try:
		return float(value)
	except (TypeError, ValueError):
		return None

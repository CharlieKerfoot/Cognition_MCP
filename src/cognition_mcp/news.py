import os

import httpx

NEWSAPI_BASE = 'https://newsapi.org/v2/everything'


async def fetch_articles(topic: str, page_size: int = 10) -> list[dict]:
	api_key = os.environ.get('NEWSAPI_KEY', '')
	if not api_key:
		raise RuntimeError(
			'NEWSAPI_KEY environment variable is not set. '
			'Get a free key at https://newsapi.org and add it to your Claude Desktop config.'
		)

	params = {
		'q': topic,
		'sortBy': 'publishedAt',
		'pageSize': page_size,
		'language': 'en',
		'apiKey': api_key,
	}

	async with httpx.AsyncClient() as client:
		response = await client.get(NEWSAPI_BASE, params=params)
		response.raise_for_status()
		data = response.json()

	if data.get('status') != 'ok':
		raise RuntimeError(f'NewsAPI error: {data.get("message", "Unknown error")}')

	articles = []
	for article in data.get('articles', []):
		articles.append(
			{
				'title': article.get('title', ''),
				'source': article.get('source', {}).get('name', ''),
				'description': article.get('description', '') or '',
				'url': article.get('url', ''),
				'published_at': article.get('publishedAt', ''),
			}
		)
	return articles

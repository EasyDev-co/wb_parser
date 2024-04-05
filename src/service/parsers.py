import logging

import requests
from django.conf import settings


class ProductPositionParser:

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(settings.HEADERS)
        self.base_url = settings.BASE_URL
        self.max_pages = settings.MAX_PAGES
        self.items_per_page = settings.ITEMS_PER_PAGE

    @staticmethod
    def _get_query_params(query: str, page: int) -> dict:
        return {
            'query': query,
            'ab_testing': 'false',
            'resultset': 'catalog',
            'limit': settings.ITEMS_PER_PAGE,
            'page': page,
            'appType': settings.APP_TYPE,
            'curr': settings.CURRENCY,
            'lang': settings.LANGUAGE,
            'dest': settings.DESTINATION,
            'spp': settings.SPP
        }

    @staticmethod
    def _find_product_position(json_data: dict | None, article: int,
                               offset: int) -> int | None:
        if json_data and not json_data.get('metadata', {}).get('is_empty'):
            products = json_data.get('data', {}).get('products', [])
            for index, product in enumerate(products):
                if product.get('id') == article:
                    return offset + index + 1
        return None

    def _fetch_json(self, query: str, page: int = 1) -> dict | None:
        params = self._get_query_params(query, page)
        try:
            response = self.session.get(self.base_url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logging.error(f"Error fetching JSON: {e}")
            return None

    def parse_position(self, query: str, article: int) -> int | None:
        for page in range(1, self.max_pages + 1):
            json_data = self._fetch_json(query, page)
            if json_data and not json_data.get('data', {}).get('products'):
                break
            position = self._find_product_position(
                json_data,
                article,
                (page - 1) * self.items_per_page
            )
            if position is not None:
                return position
        return None

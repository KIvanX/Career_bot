
import requests


def get_vacancies(query: str, filters: dict, page: int = 0):
    params = {'text': query.replace(',', ' '), 'currency': 'RUR', 'page': page, 'per_page': 1}
    if 'city' in filters:
        filters['area'] = filters.pop('city')
    params.update({key: value['id'] for key, value in filters.items()})
    res = requests.get('https://api.hh.ru/vacancies',
                       params=params,
                       headers={"Content-type": "application/json"})

    return res.json()['items']


def get_city(name: str):
    res = requests.get(f'https://api.hh.ru/suggests/area_leaves',
                       params={'text': name},
                       headers={"Content-type": "application/json"})

    return [{'id': city['id'], 'name': city['text']} for city in res.json()['items']]


# for i in range(1, 2):
#     res = requests.get(f'https://api.hh.ru/metro/{6}',
#                        # params={'city_id': i},
#                        headers={"Content-type": "application/json"})
#
#     print(res.json())

# res = requests.get('https://api.hh.ru/vacancies',
#                    params={'text': 'Python', 'area': '88'},
#                    headers={"Content-type": "application/json"})
#
# pprint(res.json())

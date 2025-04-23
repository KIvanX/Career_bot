
import requests


def hh_get_vacancies(filters: dict, page: int = 0):
    params = {'text': filters.get('knowledge', ''), 'currency': 'RUR', 'page': page, 'per_page': 1}
    if 'city' in filters:
        filters['area'] = filters.pop('city')['id']

    params.update(filters)
    res = requests.get('https://api.hh.ru/vacancies',
                       params=params,
                       headers={"Content-type": "application/json"})

    return res.json()['items']


def hh_get_city(name: str):
    res = requests.get(f'https://api.hh.ru/suggests/area_leaves',
                       params={'text': name},
                       headers={"Content-type": "application/json"})

    return [{'id': city['id'], 'name': city['text']} for city in res.json()['items']]


def stepik_get_courses(filters: dict, page: int = 0):
    params = {'query': filters.get('interests', ''), 'page': page}
    filters.pop('interests') if 'interests' in filters else None
    params.update(filters)

    res = requests.get('https://stepik.org/api/search-results', params=params)

    if 'search-results' in res.json():
        res = requests.get('https://stepik.org/api/courses',
                           params={'ids[]': [course['course'] for course in res.json()['search-results']]},
                           headers={"Content-type": "application/json"})
        return res.json()['courses']
    return []


def stepik_get_course(course_id: int):
    res = requests.get('https://stepik.org/api/courses',
                       params={'ids[]': [course_id]},
                       headers={"Content-type": "application/json"})
    return res.json()['courses'][0]


# res = requests.get(f'https://kazan.ucheba.ru/for-abiturients/speciality/search?query=программирование',
#                    headers={'content-type': 'application/json'})


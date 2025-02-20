choose_vacancy_filters = {
    'experience': [{"id": "noExperience", "name": "Нет опыта"},
                   {"id": "between1And3", "name": "От 1 года до 3 лет"},
                   {"id": "between3And6", "name": "От 3 до 6 лет"},
                   {"id": "moreThan6", "name": "Более 6 лет"}],
    'schedule': [{"id": "fullDay", "name": "Полный день", "uid": "full_day"},
                 {"id": "shift", "name": "Сменный график", "uid": "shift"},
                 {"id": "flexible", "name": "Гибкий график", "uid": "flexible"},
                 {"id": "remote", "name": "Удаленная работа", "uid": "remote"},
                 {"id": "flyInFlyOut", "name": "Вахтовый метод", "uid": "fly_in_fly_out"}],
    'employment': [{"id": "full", "name": "Полная занятость"},
                   {"id": "part", "name": "Частичная занятость"},
                   {"id": "project", "name": "Проектная работа"},
                   {"id": "volunteer", "name": "Волонтерство"},
                   {"id": "probation", "name": "Стажировка"}]
}

vacancy_filters_names = {
    'knowledge': 'Область знаний',
    'salary': 'Зарплата',
    'city': 'Город',
    'experience': 'Опыт работы',
    'schedule': 'График работы',
    'employment': 'Занятость'
}

course_filters_names = {
    'interests': 'Область интересов',
    'difficulty': 'Сложность',
    'is_paid': 'Платный',
    'with_certificate': 'Сертификат',
    'price__gte': 'Цена от',
    'price__lte': 'Цена до',
    'lang': 'Язык'
}

course_difficulty_names = {
    'easy': 'Начальный',
    'normal': 'Средний',
    'hard': 'Продвинутый'
}

get_order_prompt = '''
Ты должен узнать у пользователя, хочет ли он получить найти себе вакансию или найти курс. 

Если пользователь хочет найти работу, задавай у него вопросы по области знаний, зарплате, городу, 
опыту работы (noExperience, between1And3, between3And6, moreThan6), 
графику работы (fullDay, shift, flexible, remote, flyInFlyOut) и занятости (full, part, project, volunteer, probation). 
После верни эти данные в формате JSON. Например: {"knowledge": "Python", "salary": 100000, 
"city": "Москва", "experience": "between1And3", "schedule": "fullDay", "employment": "full"}. 

Если пользователь хочет найти курс, задавай у него вопросы по области интересов, сложности (easy, normal, hard), 
платности (true, false), наличию сертификата (true, false), цене от и до, языку. 
После верни эти данные в формате JSON. Например: {"interests": "Python", "difficulty": "normal", 
"is_paid": true, "with_certificate": true, "price__gte": 0, "price__lte": 1000, "lang": "ru"}.

Если пользователю безразличен какой-то фильтр, можешь его не возвращать. Только "knowledge" и "interests" обязательны. 
Возвращай данные в формате JSON одним сообщением без лишнего теста, до этого никаких данных в JSON выдавать не надо.
'''

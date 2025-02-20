
def get_salary(salary):
    if not salary:
        return 'Не указана'

    currency = {'RUR': '₽', 'USD': '$', 'EUR': '€'}.get(salary['currency'], salary['currency'])
    if salary['from'] and salary['to']:
        return f'{salary["from"]} - {salary["to"]} {currency}'
    elif salary['from']:
        return f'От {salary["from"]} {currency}'
    elif salary['to']:
        return f'До {salary["to"]} {currency}'

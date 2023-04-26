import pandas as pd
import statistics
import requests
import json
import keyboards
import matplotlib.pyplot as plt
import texts

pd.options.mode.chained_assignment = None

# Получение json файла с вакансиями
def api_vacancies(vacancy, region_id, page=0):
    # Задаю параметры для запроса к API
    params = {
        'text': f'name:{vacancy}',
        'area': region_id,
        'page': page,
        'per_page': 100
    }
    req = requests.get(f'https://api.hh.ru/vacancies', params)
    data = req.content.decode()
    req.close()
    return json.loads(data)  # Возвращает json файл с вакансиями


# Формирование неотсортированного датафрейма из json файла
def create_data_frame(vacancy, region_id, message):
    for page in range(20):  # Перебор страниц и группировка данных из всех доступных страниц в один датафрейм
        js_obj = api_vacancies(vacancy, region_id, page)
        if page == 0:
            df = pd.DataFrame(js_obj['items'])
        else:
            df_1 = pd.DataFrame(js_obj['items'])
            df = pd.concat([df, df_1])
        if js_obj['pages'] - page <= 1:
            break
    return df  # Возвращает неотфильтрованный датафрейм


# Поиск региона по названию в справочнике
def api_get_region(region_name):
    region_id = None
    req = requests.get('https://api.hh.ru/areas')
    data = req.content.decode()
    req.close()
    js_obj = json.loads(data)
    region_name = region_name.lower()
    for area in js_obj[0]['areas']:  # Проход по дереву
        for i in area['areas']:
            if i['name'].lower() == region_name:
                region_id = i['id']
                region_name = i['name']
                break
        if area['name'].lower() == region_name:
            region_id = area['id']
            region_name = area['name']
            break
    return region_id, region_name  # Возвращает id региона


# Фильтрация датафрейма
def filter_data_frame(df):
    df_filtered = df.dropna(subset=['salary'])
    massive_salaries_from_to = list(filter(lambda x: x is not None, df['salary']))
    massive_salaries = list(map(lambda x: x['from'] if x['from'] is not None else x['to'], massive_salaries_from_to))
    df_filtered['salaries'] = massive_salaries
    df_filtered['employers'] = list(map(lambda x: x['name'], df_filtered['employer']))
    df_filtered['snippets'] = list(map(lambda x: x['requirement'], df_filtered['snippet']))
    df_filtered['experiences'] = list(map(lambda x: x['name'], df_filtered['experience']))
    df_filtered = df_filtered[['id', 'name', 'employers', 'snippets', 'experiences', 'salaries']]
    return df_filtered  # Возвращает отфильтрованный датафрейм


# Анализ зарплат: вакансий всего, вакансий без указания зп, средняя зп по отрасли, медиана
def analysis_salaries(df, df_filtered):
    number_of_vacancies = len(df)
    number_of_vacancies_without_salary = number_of_vacancies - len(df_filtered['salaries'])
    avg_salary = int(statistics.mean(df_filtered['salaries']))
    median_salary = int(statistics.median(df_filtered['salaries']))
    return number_of_vacancies_without_salary, avg_salary, median_salary


def analysis_experience(df_filtered):
    df_filtered.groupby('experiences').salaries.mean().plot(kind='bar')
    plt.savefig('my_plot.png', bbox_inches='tight')


def top_employers(df_filtered):
    tp_employers = df_filtered.groupby('employers').id.count().head()
    return tp_employers.reset_index().sort_values('id', ascending=False)


async def analysis(message, df, vacancy, region_name):
    filtered_df = filter_data_frame(df)
    without_salary, avg, median = analysis_salaries(df, filtered_df)
    analysis_experience(filtered_df)  # построение графика опыт-зарплата
    image = 'my_plot.png'
    file = open('./' + image, 'rb')
    await message.answer_photo(file, caption=texts.analysis_text(vacancy, region_name, df, without_salary, avg, median),
                               reply_markup=keyboards.final_keyboard)

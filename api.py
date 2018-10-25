from collections import Counter
import requests
from requests import exceptions
from datetime import datetime
import plotly
import plotly.plotly as py
import plotly.graph_objs as go
import time
import networkx as nx
import community
import matplotlib.pyplot as plt
import numpy


config = {
    'vk_access_token': 'd638e6091a2063d729e6114a70850df4760487797f770694e5af975d4b55b8259a57cc481ae8d92ac6b07',
    'plotly_name': 'ilyailon',
    'plotly_key': 'RE7pthU48DxmSOwOHntL'
}

plotly.tools.set_credentials_file(username='ilyailon', api_key='RE7pthU48DxmSOwOHntL')

def get(url, params={}, timeout=5, max_retries=5, backoff_factor=0.3):
    """ Выполнить GET-запрос
    :param url: адрес, на который необходимо выполнить запрос
    :param params: параметры запроса
    :param timeout: максимальное время ожидания ответа от сервера
    :param max_retries: максимальное число повторных запросов
    :param backoff_factor: коэффициент экспоненциального нарастания задержки
    """
    for attempt in range(max_retries):
        try:
            return requests.get(url, params=params, timeout=timeout)
        except requests.exceptions.RequestException:
            if attempt == max_retries - 1:
                raise
            delay = backoff_factor * (2 ** (attempt - 1))
            time.sleep(delay)


def get_friends(user_id, fields):
    """ Returns a list of user IDs or detailed information about a user's friends """
    assert isinstance(user_id, int), "user_id must be positive integer"
    assert isinstance(fields, str), "fields must be string"
    assert user_id > 0, "user_id must be positive integer"

    query_params = {
        'domain': "https://api.vk.com/method",
        'access_token': config['vk_access_token'],
        'user_id': user_id,
        'fields': fields
    }

    query = "{domain}/friends.get?access_token={access_token}&user_id={user_id}&fields={fields}&v=5.53".format(**query_params)
    response = get(query, query_params)
    return response


def age_predict(user_id):
    
    assert isinstance(user_id, int), "user_id must be positive integer"
    assert user_id > 0, "user_id must be positive integer"

    response = get_friends(user_id, 'bdate')
    if (response.json()).get('error'):
            return print('User was banned or deleted!')
    age, numfriends, nfriend = 0, 0, 0
    now = str(datetime.now())
    year_now = int(now[0:4])
    month_now = int(now[5:7])
    day_now = int(now[8:10])
    for friend in response.json()['response']['items']:
        if 'bdate' in friend:
            bdate = response.json()['response']['items'][nfriend]['bdate']
            if bdate.count('.') == 2:
                day = bdate[:bdate.find('.'):]
                bdate = bdate[len(day)+1:]
                month = bdate[:bdate.find('.'):]
                year = bdate[len(month)+1::]
                age += year_now - int(year)
                if (day_now < int(day) and month_now == int(month))\
                        or (month_now < int(month)):
                    age -= 1
                numfriends += 1
        nfriend += 1
    return age//numfriends


def messages_get_history(user_id, offset=0, count=20):

    assert isinstance(user_id, int), "user_id must be positive integer"
    assert user_id > 0, "user_id must be positive integer"
    assert isinstance(offset, int), "offset must be positive integer"
    assert offset >= 0, "user_id must be positive integer"
    assert count >= 0, "user_id must be positive integer"

    query_params = {
        'domain': "https://api.vk.com/method",
        'access_token': config['vk_access_token'],
        'user_id': user_id,
        'offset': offset
    }

    messages = []
    while count:
        if count > 200:
            query_params['count'] = 200
            count -= 200
        else:
            query_params['count'] = count
            count -= count
        query = "{domain}/messages.getHistory?offset={offset}&count={count}&user_id={user_id}&access_token={access_token}&v=5.53".format(**query_params)
        response = get(query, query_params)
        for col in range(len(response.json()['response']['items'])):
            messages.append(response.json()['response']['items'][col])
        query_params['offset'] += 200
        time.sleep(0.5)
    return messages


def count_dates_from_messages(messages):
    
    date = [datetime.fromtimestamp(messages[message]['date']).strftime("%Y-%m-%d")
            for message in range(len(messages))]
    freq_dates = Counter(date)
    dates = list(freq_dates.keys())
    frequency = list(freq_dates.values())
    return dates, frequency


def plotly_messages_freq(freq_list):
    
    x, y = freq_list
    data = [go.Scatter(x=x, y=y)]
    py.plot(data)


def get_network(users_ids, as_edgelist=True):
    """ Building a friend graph for an arbitrary list of users """
    edgelist = []
    matrix = [[0 for col in range(len(users_ids))]
              for row in range(len(users_ids))]
    for x, user_id in enumerate(users_ids):
        response = get_friends(user_id, fields='bdate')
        if (response.json()).get('error'):
            continue
        frinds_of_friend = []
        nfriend = 0
        for friend in response.json()['response']['items']:
            id_of_user = response.json()['response']['items'][nfriend]['id']
            frinds_of_friend.append(id_of_user)
            nfriend += 1
        for y in range(x + 1, len(users_ids)):
            if users_ids[y] in frinds_of_friend:
                if as_edgelist:
                    edgelist.append((x, y))
                else:
                    matrix[x][y] = matrix[y][x] = 1
    if as_edgelist:
        return edgelist
    else:
        return matrix


def plot_graph(graph):
    nodes = set([n for n, m in graph] + [m for n, m in graph])
    g = nx.Graph()
    for node in nodes:
        g.add_node(node)
    for edge in graph:
        g.add_edge(edge[0], edge[1])
    pos = nx.shell_layout(g)
    part = community.best_partition(g)
    values = [part.get(node) for node in g.nodes()]
    nx.draw_spring(g, cmap=plt.get_cmap('jet'), node_color=values,
                   node_size=30, with_labels=False)
    plt.show()


if __name__ == '__main__':
    user_id = 25272190
    friend_id = 18870987
    print('Age: ', age_predict(user_id))

    messages = messages_get_history(friend_id, offset=0, count=300)
    data = count_dates_from_messages(messages)
    plotly_messages_freq(data)

    response = get_friends(user_id, fields='user_id')
    friend = response.json()['response']['items']
    friends_ids = [friend[nfriend]['id'] for nfriend in range(len(friend))]
    edges = get_network(friends_ids)
    plot_graph(edges)

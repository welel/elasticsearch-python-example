from datetime import datetime

from elasticsearch import Elasticsearch, helpers

from settings import ELASTIC_DSN


INDEX_NAME = "user_2"

# Соединение с Эластиком, все запросы выполняются через него.
# DSN = "http://<username>:<password>@<host>:<port>/"
es = Elasticsearch(ELASTIC_DSN)


def create_index():
    """Создание индеса."""

    # Тело запроса точно такое же как и сырой запрос в Kibana.
    request_body = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0
        },
        "mappings": {
            "properties": {
                "name": {
                    "type": "text",
                    "fields": {
                        "keyword": {
                            "type": "keyword"
                        }
                    }
                },
                "age": {
                    "type": "integer"
                },
                "created_at": {
                    "type": "date"
                }
            }
        }
    }

    # В ответе будет точно такой же ответ как наблюдаем в Kibana,
    # но с некоторой дополнительной информацией о запросе.
    response = es.indices.create(index=INDEX_NAME, body=request_body)
    
    # В некоторых запросах, где тело запроса делится на логические блоки,
    # как здесь - на settings и mappings, метод позволяет тело запроса
    # передавать по логическим частям. Это может быть удобно, например,
    # если мы загружаем mappings из файла.
    
    # es.indices.create(index=INDEX_NAME, settings={}, mappings={})

    return response


def add_doc():
    """Добавление документа в индекс."""

    doc = {"name": "John Doe", "age": 30, "created_at": datetime.now()}
    
    # Если заглянуть в экземпляр es, видно, что у него есть методы create
    # и update, но удобнее использовать index, который сам выбирает какую
    # операцию применить.

    return es.index(index=INDEX_NAME, id=1, body=doc)


def add_docs():
    """Добавление документов в индекс за один запрос."""
    
    # Имеем набор документов. Необходимо добавить информацию об операции,
    # индекс и ID документа.

    docs = [
        {"name": "Kale Smith", "age": 19, "created_at": "2022-01-01T00:00:00"},
        {"name": "John Blake", "age": 25, "created_at": "2022-02-01T00:00:00"},
        {"name": "Raul Perez", "age": 31, "created_at": "2022-03-01T00:00:00"},
        {"name": "Ton Walker", "age": 44, "created_at": "2022-04-01T00:00:00"},
        {"name": "Just Blake", "age": 59, "created_at": "2022-05-01T00:00:00"},
    ]

    # Если в сыром HTTP запросе передаётся две строчки на объект - meta + doc,
    # то тут это выглядит следующим образом, один action представляет одну
    # операцию. В action задаётся название индекса, тип операции, ID, документ.

    actions = []
    for i, doc in enumerate(docs):
        action = {
            "_index": INDEX_NAME,
            "_op_type": "index",
            "_id": i,
            "_source": doc
        }
        actions.append(action)

    # В actions описано что необходимо сделать с каждым из документов, теперь
    # просто вызываем bulk операцию.

    return helpers.bulk(es, actions)


def search_doc():
    """Поиск документов."""

    # Запрос ничем не отличается от запроса в Kibana, можно передавать
    # полный запрос в параметр body или бить на логические кусочки: 
    # source, size, query и так далее.

    # Так как это базовый драйвер тут нет удобного ORM для составления
    # запросов на поиск. Как их формировать зависит от фантазии и времени,
    # можно хардкодить запросы, написать собственную библиотечку или
    # динамически формировать при помощи набора функций.

    # Существует библиотека от создателей базового драйвера для составления
    # запросов - Elasticsearch DSL. Можно попробовать её.
    # https://elasticsearch-dsl.readthedocs.io/en/latest/

    response = es.search(
        index=INDEX_NAME,
        source=["name"],
        size=2,
        query={
            "bool": {
                "should": [
                    {"match": {"name": "Blake"}},
                    {"match": {"name": "Kale"}}
                ]
            }
        },
        sort=[{"age": {"order": "desc"}}]
    )
    return [hit["_source"] for hit in response["hits"]["hits"]]


# Примеры остальных операций можно посмотреть в документации драйвера:
# https://elasticsearch-py.readthedocs.io/en/v8.10.1/quickstart.html


if __name__ == "__main__":
    print(1)

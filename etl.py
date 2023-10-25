from elasticsearch import Elasticsearch, helpers

import psycopg2
from psycopg2.extras import RealDictCursor

from settings import ELSTIC_DSN, PG_DSN


class PostgreSQLExtractor:

    db_conncetion = psycopg2.connect(PG_DSN, cursor_factory=RealDictCursor)

    def get_generator_from_query(self, query, itersize):
        """Gets a generator of rows for a given query.

        Args:
            query (str): The SQL query to execute.
            itersize (int): The number of rows to fetch at a time in cursor.

        Yields:
            dict: Next row.
        """
        # О том, как сделать Server-Side cursor:
        # https://www.psycopg.org/psycopg3/docs/advanced/cursors.html#server-side-cursors

        cursor = self.db_connection.cursor()
        cursor.itersize = itersize
        cursor.execute(query)

        try:
            for row in cursor:
                
                # row является dict'ом, т.к. при создании соединения был
                # передан параметр cursor_factory со значением RealDictCursor.
                
                yield row
        finally:
            cursor.close()


class ElasticsearchLoader:

    es_conncetion = Elasticsearch(ELSTIC_DSN)

    def index_docs(self, docs, index, op_type, id_func):
        """Index documents into a index.

        Args:
            docs (list[dict]): A list of docs to be indexed.
            index (str): The index name.
            op_type (str): The operation type for documents.
            id_func (Callable): The doc id extractor.
        """
        actions = []
        for doc in docs:
            actions.append({
                "_op_type": op_type,
                "_index": index,
                "_id": id_func(doc),
                "_source": doc,
            })

        helpers.bulk(self.es_conncetion, actions)


def etl_products():

    INDEX_NAME = "product"

    # Имеем два класса для работы с данными. Каждый класс имеет набор методов
    # для работы с данными: extractor - функционал для извлечения данных из
    # БД, а loader - функционал для загрузки данных в Эластик.

    # Трансформация данных может происходить в одном из этих классов,
    # или в валидаторе или прямо в функции начитки, если необходимо.

    extractor = PostgreSQLExtractor()
    loader = ElasticsearchLoader()

    # Создаем индекс для начитки.

    loader.create_index(INDEX_NAME)

    # Имеем некоторый SQL запрос, для извлечения данных. Одна строка
    # результата этого запроса является одним документом, который
    # необходимо загрузить в индекс. Представим, что это запрос
    # продуктов из БД.

    QUERY = """Сырой SQL запрос, который запрашивает продкуты из БД."""
    
    LOAD_BATCH_SIZE = 10_000

    # Создаём генератор, который возвращает по одному продукту в dict формате.

    products_gen = extractor.get_generator_from_query(
        QUERY, itersize=LOAD_BATCH_SIZE
    )

    # Запускаем цикл начитки индекса. Этот цикл должен проитерироваться
    # по всем строкам запроса QUERY. И начитать результаты в индекс.

    product_docs = []  # Буфер документов

    for product in products_gen:

        # Некоторая трансформация документа, если требуется.

        product_docs.append(product)

        # По достижению в буфере LOAD_BATCH_SIZE, выполняется запрос на
        # индексацию.

        if len(product_docs) and len(product_docs) % LOAD_BATCH_SIZE == 0:

            loader.index_docs(
                product_docs,
                index=INDEX_NAME,
                op_type="index",
                id_func=lambda doc: doc["uuid"],
            )
            product_docs.clear()

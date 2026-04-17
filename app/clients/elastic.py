from elasticsearch import Elasticsearch
import os

es = Elasticsearch(os.getenv("ES_URI", "http://elasticsearch:9200"))
es_index = "products"

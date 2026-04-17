from elasticsearch import Elasticsearch
import os

es = Elasticsearch(os.getenv("ES_URI", "http://elastic:9200"))
es_index = "products"

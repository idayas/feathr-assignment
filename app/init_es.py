from clients import es

INDEX = "products"

def init_elasticsearch():
    if es.indices.exists(index=INDEX):
        return

    es.indices.create(index=INDEX, body={
        "mappings": {
            "properties": {
                "ProductId":          { "type": "keyword" },
                "ProductName":        { "type": "text" },
                "ProductCategory":    { "type": "keyword" },
                "Price":              { "type": "float" },
                "AvailableQuantity":  { "type": "integer" },
                "ProductDescription": { "type": "text" }
            }
        }
    })

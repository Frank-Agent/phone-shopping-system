import httpx
import json

api_key = 'FF35244DF73B4E768344D053EB9CDDB9'
asin = 'B0FJMH7RBK'  # Google Pixel 10

url = 'https://api.rainforestapi.com/request'
params = {
    'api_key': api_key,
    'type': 'product',
    'amazon_domain': 'amazon.com',
    'asin': asin
}

response = httpx.get(url, params=params, timeout=30.0)
data = response.json()
product = data.get('product', {})

print('Product variants from API:')
variants = product.get('variants', [])
print(f'Total variant groups: {len(variants)}')

for i, variant_group in enumerate(variants[:3], 1):
    print(f'\nVariant Group {i}: {variant_group.get("dimension", "Unknown")}')
    for value in variant_group.get('values', [])[:5]:
        print(f'  - {value.get("value", "N/A")}')
        print(f'    ASIN: {value.get("asin", "N/A")}')
        print(f'    Available: {value.get("is_available", False)}')
        if value.get('price'):
            print(f'    Price: ${value["price"].get("value", 0)}')
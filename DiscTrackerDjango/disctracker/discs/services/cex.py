import requests

def fetch_item(cex_id):
    search_url = f'https://wss2.cex.uk.webuy.io/v3/boxes/{cex_id}/detail'
    response = requests.get(search_url)
    if response.status_code == 200:
        try:
            data = response.json()
            return data['response']['data']
        except:
            print('Failed to parse JSON response')
            return None
    else:
        print('Failed To Fetch Item')
        return None
    
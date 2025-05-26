from bs4 import BeautifulSoup
import requests

url = "https://deadbydaylight.wiki.gg/wiki/Category:Killers"
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

# Seleciona todos os links para as subcategorias
subcat_links = soup.select("div#mw-subcategories a")
for link in subcat_links:
    print(link['href'], "-", link.text)

base_url = "https://deadbydaylight.wiki.gg"
killer_urls = []

for link in subcat_links:
    sub_url = base_url + link['href']
    res = requests.get(sub_url)
    sub_soup = BeautifulSoup(res.text, 'html.parser')

    killer_links = sub_soup.select("div.mw-category-generated a")
    for k in killer_links:
        killer_urls.append(base_url + k['href'])

# Agora você tem a URL de todos os killers
for url in killer_urls:
    print(url)

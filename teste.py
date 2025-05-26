from bs4 import BeautifulSoup
import requests

url_base= 'https://deadbydaylight.wiki.gg'
html_text = requests.get(url_base).text
soup = BeautifulSoup(html_text, 'lxml')

killer_tab = soup.select_one('article#Killers-0')
survivor_tab = soup.select_one('article#Survivors-0')

killer_links = killer_tab.select("div.charPortraitImage a")
survivor_links = survivor_tab.select("div.charPortraitImage a")


import requests
from bs4 import BeautifulSoup

def perk_scraper(link):
    res = requests.get(link)
    soup = BeautifulSoup(res.text, 'lxml')




def scrap_killer_details(link):
    res = requests.get(link)
    soup = BeautifulSoup(res.text, 'lxml')

    # Informações da tabela
    table = soup.select_one('table.infoboxtable.charInfoboxTable.killerInfobox')
    if not table:
        print("Nenhuma tabela encontrada")
        return
    info = {}
    for row in table.select('tr'):
        cols = row.find_all(['th', 'td'])
        if len(cols) == 2:
            key = ' '.join(cols[0].get_text(strip=True).split())
            value = ' '.join(cols[1].get_text(strip=True).split())
            info[key] = value
    apelido = soup.select_one('th.bold').text.strip()
    # Se não tiver nome real, usa o apelido
    real_name = info.get('Name')
    if not real_name or real_name.lower() == apelido.lower():
        real_name = apelido
    dlc = info.get('DLC', 'Base')




    print(f'Nome: {real_name}, Apelido: {apelido}, DLC: {dlc}')


def scrap_survivor_details(link):
    res = requests.get(link)
    soup = BeautifulSoup(res.text, 'lxml')

    # Informações da tabela
    table = soup.select_one('table.infoboxtable.charInfoboxTable.survivorInfobox')
    if not table:
        print("Nenhuma tabela encontrada")
        return
    info = {}
    for row in table.select('tr'):
        cols = row.find_all(['th', 'td'])
        if len(cols) == 2:
            key = ' '.join(cols[0].get_text(strip=True).split())
            value = ' '.join(cols[1].get_text(strip=True).split())
            info[key] = value

    # Se não tiver nome real, usa o apelido
    name = soup.select_one('th.bold').text.strip()
    gender = info.get('Gender')
    origin = info.get('Origin')
    role = info.get('Role')
    dlc = info.get('DLC', 'Base')

    print(f'Nome: {name}, Genero: {gender}, Role:{role}, DLC: {dlc}')

def killers_scrap():
    for killer in killer_links:
        link_relative = killer.get('href')
        links_completo = url_base + link_relative
        scrap_killer_details(links_completo)
def survivor_scrap():
    for survivor in survivor_links:
        link_relative = survivor.get('href')
        links_completo = url_base + link_relative
        scrap_survivor_details(links_completo)


def main():
    #survivor_scrap()
    print(' ')
    #killers_scrap()

    taurie = perk_scraper('https://deadbydaylight.wiki.gg/wiki/Taurie_Cain')
    trapper = perk_scraper('https://deadbydaylight.wiki.gg/wiki/Evan_MacMillan')

    print(taurie)
    print(trapper)

if __name__ == '__main__':
    main()
# dbd_scraper.py
from bs4 import BeautifulSoup
import requests
import time
import random

url_base = 'https://deadbydaylight.wiki.gg'


def get_character_links():
    """Obtém links de todos os personagens"""
    html_text = requests.get(url_base).text
    soup = BeautifulSoup(html_text, 'lxml')

    killer_tab = soup.select_one('article#Killers-0')
    survivor_tab = soup.select_one('article#Survivors-0')

    killer_links = [url_base + a['href'] for a in killer_tab.select("div.charPortraitImage a")]
    survivor_links = [url_base + a['href'] for a in survivor_tab.select("div.charPortraitImage a")]

    return killer_links, survivor_links


def perk_scraper(link):
    """Extrai perks de um personagem"""
    try:
        res = requests.get(link)
        soup = BeautifulSoup(res.text, 'lxml')
        perks = []

        # Encontrar a tabela de perks
        perks_header = soup.find(lambda tag: tag.name in ['h2', 'h3'] and 'Perks' in tag.text)
        if not perks_header:
            return perks

        table = perks_header.find_next('table', class_='wikitable')
        if not table:
            return perks

        for row in table.find_all('tr')[1:4]:  # Apenas 3 perks
            cols = row.find_all(['th', 'td'])
            if len(cols) < 3:
                continue

            name_link = cols[1].find('a')
            perk_name = name_link.text.strip() if name_link else cols[1].text.strip()

            perks.append(perk_name)

        return perks

    except Exception as e:
        print(f"Erro ao extrair perks: {e}")
        return []


def scrap_killer(link):
    """Processa um assassino"""
    try:
        res = requests.get(link)
        soup = BeautifulSoup(res.text, 'lxml')

        # Informações básicas
        alias = soup.select_one('th.bold').text.strip()

        # Tabela de informações
        info = {}
        table = soup.select_one('table.infoboxtable.charInfoboxTable.killerInfobox')
        if table:
            for row in table.select('tr'):
                cols = row.find_all(['th', 'td'])
                if len(cols) == 2:
                    key = cols[0].get_text(strip=True)
                    value = cols[1].get_text(strip=True)
                    info[key] = value

        real_name = info.get('Name', alias)
        power = info.get('Power', 'N/A')
        dlc = info.get('DLC', 'Base')

        # Perks
        perks = perk_scraper(link)

        return {
            'name': real_name,
            'alias': alias,
            'power': power,
            'dlc': dlc,
            'perks': perks,
            'link': link
        }

    except Exception as e:
        print(f"Erro ao processar assassino: {e}")
        return None


def main():
    """Função principal"""
    print("Iniciando coleta de dados...")
    killers, survivors = get_character_links()

    # Coletar assassinos
    killers_data = []
    for link in killers:
        print(f"Processando: {link}")
        killer_data = scrap_killer(link)
        if killer_data:
            killers_data.append(killer_data)
            print(f"Coletado: {killer_data['alias']}")
        time.sleep(random.uniform(1, 3))  # Evitar bloqueio

    # Exibir resultados
    print("\nResultados:")
    for killer in killers_data:
        print(f"{killer['alias']} ({killer['name']}):")
        print(f"  Poder: {killer['power']}")
        print(f"  Perks: {', '.join(killer['perks'])}")
        print()


if __name__ == '__main__':
    main()

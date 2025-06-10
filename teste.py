from bs4 import BeautifulSoup
import requests

url_base= 'https://deadbydaylight.wiki.gg'
html_text = requests.get(url_base).text
soup = BeautifulSoup(html_text, 'lxml')

killer_tab = soup.select_one('article#Killers-0')
survivor_tab = soup.select_one('article#Survivors-0')

killer_links = killer_tab.select("div.charPortraitImage a")
survivor_links = survivor_tab.select("div.charPortraitImage a")

def power_scraper(link):
    res = requests.get(link)
    soup = BeautifulSoup(res.text, 'lxml')




def perk_scraper(link):
    try:
        res = requests.get(link)
        soup = BeautifulSoup(res.text, 'lxml')
        perks = []

        # Abordagem alternativa para encontrar a tabela de perks
        # Procurar por tabelas que contenham o texto "Perk" em algum lugar
        tables = soup.find_all('table', class_='wikitable')
        perk_table = None

        for table in tables:
            if table.find(string="Perk") or table.find(string="Perks"):
                perk_table = table
                break

        if not perk_table:
            # Tentar por cabeçalho
            perks_header = soup.find(lambda tag: tag.name in ['h2', 'h3'] and 'Perks' in tag.text)
            if perks_header:
                perk_table = perks_header.find_next('table', class_='wikitable')

        if not perk_table:
            return perks

        # Processar todas as linhas válidas (ignorando cabeçalhos)
        for row in perk_table.find_all('tr'):
            # Verificar se a linha contém uma perk (deve ter pelo menos 3 colunas)
            if len(row.find_all(['th', 'td'])) < 3:
                continue

            # Verificar se a linha contém um ícone de perk
            if not row.find('img', alt=lambda x: x and 'IconPerks' in x):
                continue

            cols = row.find_all(['th', 'td'])

            # Ícone da perk
            icon = cols[0].find('img')
            icon_url = url_base + icon['src'] if icon else None

            # Nome da perk
            name_link = cols[1].find('a')
            perk_name = name_link.text.strip() if name_link else cols[1].get_text(strip=True)

            # Descrição completa
            description = ""
            for element in cols[2].contents:
                if isinstance(element, str):
                    description += element.strip() + " "
                elif element.name in ['i', 'b']:
                    description += element.get_text(strip=True) + " "
                elif element.name == 'ul':
                    for li in element.find_all('li'):
                        description += li.get_text(strip=True) + " "
            description = ' '.join(description.split())

            perks.append({
                'name': perk_name,
                'description': description,
                'icon': icon_url
            })

            # Limitar a 3 perks por personagem
            if len(perks) >= 3:
                break

        return perks

    except Exception as e:
        print(f"Erro ao extrair perks de {link}: {e}")
        return []


def scrap_killer_details(link):
    res = requests.get(link)
    soup = BeautifulSoup(res.text, 'lxml')

    # Informações da tabela
    table = soup.select_one('table.infoboxtable.charInfoboxTable.killerInfobox')
    if not table:
        print("Nenhuma tabela encontrada")
        return None

    info = {}
    power_link = None  # Inicializa a variável para o link do poder

    for row in table.select('tr'):
        cols = row.find_all(['th', 'td'])
        if len(cols) == 2:
            key = ' '.join(cols[0].get_text(strip=True).split())
            value = ' '.join(cols[1].get_text(strip=True).split())
            info[key] = value

            # Verifica se é a linha do Power e extrai o link
            if key == 'Power':
                power_anchor = cols[1].find('a')
                if power_anchor and power_anchor.has_attr('href'):
                    power_link = power_anchor['href']
                    # Converte para URL absoluta se necessário
                    if not power_link.startswith('http'):
                        base_url = "https://deadbydaylight.fandom.com"
                        power_link = base_url + power_link

    apelido = soup.select_one('th.bold').text.strip()

    # Se não tiver nome real, usa o apelido
    real_name = info.get('Name', apelido)

    dlc = info.get('DLC', 'Base')
    power_name = info.get('Power', 'Unknown')

    # Extrair perks
    perks = perk_scraper(link)
    perk_names = [perk['name'] for perk in perks] if perks else []

    # Retorna todos os dados incluindo o link do power
    return {
        'nickname': apelido,
        'real_name': real_name,
        'dlc': dlc,
        'power_name': power_name,
        'power_link': power_link,  # Link extraído
        'perks': perk_names
    }

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

    perk_scraper(link)

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


    #print(scrap_killer_details('https://deadbydaylight.wiki.gg/wiki/Evan_MacMillan'))

    #taurie = perk_scraper('https://deadbydaylight.wiki.gg/wiki/Taurie_Cain')
    #trapper = perk_scraper('https://deadbydaylight.wiki.gg/wiki/Evan_MacMillan')

    print(power_scraper('https://deadbydaylight.wiki.gg/wiki/Evan_MacMillan'))

    #print(taurie)
    #print(trapper)

if __name__ == '__main__':
    main()
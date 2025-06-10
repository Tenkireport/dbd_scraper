import os
import psycopg2
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv # Importe a biblioteca
load_dotenv()
# --- SEU CÓDIGO DE SETUP DA BEAUTIFULSOUP ---
url_base = 'https://deadbydaylight.wiki.gg'

try:
    html_text = requests.get(url_base).text
    soup = BeautifulSoup(html_text, 'lxml')
    killer_tab = soup.select_one('article#Killers-0')
    survivor_tab = soup.select_one('article#Survivors-0')
    killer_links = killer_tab.select("div.charPortraitImage a")
    survivor_links = survivor_tab.select("div.charPortraitImage a")
except Exception as e:
    print(f"Erro inicial ao carregar a página principal: {e}")
    killer_links = []
    survivor_links = []


# --- FUNÇÃO perk_scraper ATUALIZADA ---
def perk_scraper(link):
    """
    Extrai os detalhes das perks de uma página de personagem.
    Utiliza uma abordagem mais genérica para encontrar a tabela de perks
    e limita a 3 perks por personagem.
    """
    try:
        res = requests.get(link)
        res.raise_for_status()  # Lança um erro HTTP para respostas ruins (4xx ou 5xx)
        soup = BeautifulSoup(res.text, 'lxml')
        perks = []

        # Abordagem alternativa para encontrar a tabela de perks
        # Procurar por tabelas que contenham o texto "Perk" em algum lugar
        tables = soup.find_all('table', class_='wikitable')
        perk_table = None

        for table in tables:
            # Verifica se a tabela contém a palavra "Perk" ou "Perks"
            if table.find(string="Perk") or table.find(string="Perks"):
                perk_table = table
                break

        if not perk_table:
            # Se não encontrou pela string, tenta por cabeçalho
            perks_header = soup.find(lambda tag: tag.name in ['h2', 'h3'] and 'Perks' in tag.text)
            if perks_header:
                # Procura a primeira tabela com classe 'wikitable' após o cabeçalho
                perk_table = perks_header.find_next('table', class_='wikitable')

        if not perk_table:
            return perks  # Retorna lista vazia se nenhuma tabela de perks for encontrada

        # Processar todas as linhas válidas (ignorando cabeçalhos)
        for row in perk_table.find_all('tr'):
            # Verificar se a linha contém uma perk (deve ter pelo menos 3 colunas)
            # e se contém um ícone de perk, o que é um bom indicador
            cols = row.find_all(['th', 'td'])
            if len(cols) < 3 or not row.find('img', alt=lambda x: x and 'IconPerks' in x):
                continue

            # Ícone da perk (primeira coluna)
            icon = cols[0].find('img')
            icon_url = url_base + icon['src'] if icon and icon.has_attr('src') else None

            # Nome da perk (segunda coluna)
            name_link = cols[1].find('a')
            perk_name = name_link.text.strip() if name_link else cols[1].get_text(strip=True)

            # Descrição completa (terceira coluna)
            description = ""
            for element in cols[2].contents:
                if isinstance(element, str):
                    description += element.strip() + " "
                elif element.name in ['i', 'b', 'span']:  # Adicionado 'span' para robustez
                    description += element.get_text(strip=True) + " "
                elif element.name == 'ul':
                    for li in element.find_all('li'):
                        description += li.get_text(strip=True) + " "
            description = ' '.join(description.split()).strip()  # Normaliza espaços

            perks.append({
                'name': perk_name,
                'description': description,
                'icon': icon_url
            })

            # Limitar a 3 perks por personagem, conforme especificado
            if len(perks) >= 3:
                break

        return perks

    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar perks de {link}: {e}")
        return []
    except Exception as e:
        print(f"Erro ao extrair perks de {link}: {e}")
        return []


def scrap_killer_details(link):
    """
    Extrai os detalhes de um assassino (sem os detalhes completos do poder).
    """
    try:
        res = requests.get(link)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'lxml')

        table = soup.select_one('table.infoboxtable.charInfoboxTable.killerInfobox')
        if not table:
            print(f"Nenhuma tabela de informações encontrada para o assassino em {link}")
            return None

        info = {}
        power_link = None

        for row in table.select('tr'):
            cols = row.find_all(['th', 'td'])
            if len(cols) == 2:
                key = ' '.join(cols[0].get_text(strip=True).split())
                value = ' '.join(cols[1].get_text(strip=True).split())
                info[key] = value

                if key == 'Power':
                    power_anchor = cols[1].find('a')
                    if power_anchor and power_anchor.has_attr('href'):
                        power_link = url_base + power_anchor['href']

        apelido = soup.select_one('th.bold').text.strip()
        real_name = info.get('Name', apelido)
        dlc = info.get('DLC', 'Base')
        power_name = info.get('Power', 'Unknown')

        power_details = {}

        perks = perk_scraper(link)

        return {
            'nickname': apelido,
            'real_name': real_name,
            'dlc': dlc,
            'power_name': power_name,
            'power_link': power_link,
            'power_details': power_details,
            'perks': perks
        }
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar detalhes do assassino em {link}: {e}")
        return None
    except Exception as e:
        print(f"Erro ao extrair detalhes do assassino de {link}: {e}")
        return None


def scrap_survivor_details(link):
    """
    Extrai os detalhes de um sobrevivente.
    Retorna um dicionário com os detalhes do sobrevivente e suas perks.
    """
    try:
        res = requests.get(link)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'lxml')

        table = soup.select_one('table.infoboxtable.charInfoboxTable.survivorInfobox')
        if not table:
            print(f"Nenhuma tabela de informações encontrada para o sobrevivente em {link}")
            return None
        info = {}
        for row in table.select('tr'):
            cols = row.find_all(['th', 'td'])
            if len(cols) == 2:
                key = ' '.join(cols[0].get_text(strip=True).split())
                value = ' '.join(cols[1].get_text(strip=True).split())
                info[key] = value

        name = soup.select_one('th.bold').text.strip()
        gender = info.get('Gender')
        origin = info.get('Origin')
        role = info.get('Role')
        dlc = info.get('DLC', 'Base')

        perks = perk_scraper(link)

        return {
            'name': name,
            'gender': gender,
            'origin': origin,
            'role': role,
            'dlc': dlc,
            'perks': perks
        }
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar detalhes do sobrevivente em {link}: {e}")
        return None
    except Exception as e:
        print(f"Erro ao extrair detalhes do sobrevivente de {link}: {e}")
        return None


def killers_scrap():
    """
    Coordena a raspagem de todos os assassinos.
    """
    all_killers_data = []
    print("Iniciando raspagem de assassinos...")
    for killer in killer_links:
        link_relative = killer.get('href')
        links_completo = url_base + link_relative
        print(f"Raspando: {links_completo}")
        killer_data = scrap_killer_details(links_completo)
        if killer_data:
            all_killers_data.append(killer_data)
    print("Raspagem de assassinos concluída.")
    return all_killers_data


def survivor_scrap():
    """
    Coordena a raspagem de todos os sobreviventes.
    """
    all_survivors_data = []
    print("Iniciando raspagem de sobreviventes...")
    for survivor in survivor_links:
        link_relative = survivor.get('href')
        links_completo = url_base + link_relative
        print(f"Raspando: {links_completo}")
        survivor_data = scrap_survivor_details(links_completo)
        if survivor_data:
            all_survivors_data.append(survivor_data)
    print("Raspagem de sobreviventes concluída.")
    return all_survivors_data


# --- Configuração do Banco de Dados PostgreSQL ---

# SUBSTITUA PELA SUA STRING DE CONEXÃO DO SUPABASE
SUPABASE_CONNECTION_STRING = os.getenv("SUPABASE_CONNECTION_STRING")

# Verificação básica para garantir que a string foi carregada
if not SUPABASE_CONNECTION_STRING:
    raise ValueError("A variável de ambiente 'SUPABASE_CONNECTION_STRING' não está definida. Verifique seu arquivo .env.")

def get_db_connection():
    """
    Estabelece e retorna uma conexão com o banco de dados PostgreSQL.
    """
    try:
        conn = psycopg2.connect(SUPABASE_CONNECTION_STRING)
        return conn
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados Supabase: {e}")
        return None


def setup_database():
    """
    Cria as tabelas no banco de dados PostgreSQL se elas não existirem.
    """
    conn = get_db_connection()
    if conn is None:
        return

    cursor = conn.cursor()

    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS killers (
                id SERIAL PRIMARY KEY,
                nickname TEXT NOT NULL,
                real_name TEXT,
                dlc TEXT,
                power_name TEXT,
                power_link TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS perks (
                id SERIAL PRIMARY KEY,
                character_id INTEGER NOT NULL,
                character_type TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                icon_url TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS survivors (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                gender TEXT,
                origin TEXT,
                role TEXT,
                dlc TEXT
            )
        ''')

        conn.commit()
        print("Banco de dados Supabase configurado com sucesso!")

    except Exception as e:
        conn.rollback()
        print(f"Erro ao configurar o banco de dados: {e}")
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


def insert_killer_data(killer_data):
    """
    Insere os dados de um assassino no banco de dados Supabase.
    """
    conn = get_db_connection()
    if conn is None:
        return None
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id FROM killers WHERE nickname = %s", (killer_data['nickname'],))
        existing_killer = cursor.fetchone()

        killer_id = None
        if existing_killer:
            killer_id = existing_killer[0]
            print(f"Assassino '{killer_data['nickname']}' já existe. Verificando perks.")
        else:
            cursor.execute('''
                INSERT INTO killers (nickname, real_name, dlc, power_name, power_link)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id;
            ''', (killer_data['nickname'], killer_data['real_name'],
                  killer_data['dlc'], killer_data['power_name'], killer_data['power_link']))

            killer_id = cursor.fetchone()[0]
            print(f"Assassino '{killer_data['nickname']}' inserido com sucesso!")

        for perk in killer_data['perks']:
            cursor.execute("SELECT id FROM perks WHERE character_id = %s AND character_type = %s AND name = %s",
                           (killer_id, 'killer', perk['name']))
            existing_perk = cursor.fetchone()
            if not existing_perk:
                cursor.execute('''
                    INSERT INTO perks (character_id, character_type, name, description, icon_url)
                    VALUES (%s, %s, %s, %s, %s);
                ''', (killer_id, 'killer', perk['name'], perk['description'], perk['icon']))

        conn.commit()
        return killer_id

    except Exception as e:
        conn.rollback()
        print(f"Erro ao inserir/atualizar dados do assassino '{killer_data['nickname']}': {e}")
        return None
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


def insert_survivor_data(survivor_data):
    """
    Insere os dados de um sobrevivente e suas perks no banco de dados Supabase.
    """
    conn = get_db_connection()
    if conn is None:
        return None
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id FROM survivors WHERE name = %s", (survivor_data['name'],))
        existing_survivor = cursor.fetchone()

        survivor_id = None
        if existing_survivor:
            survivor_id = existing_survivor[0]
            print(f"Sobrevivente '{survivor_data['name']}' já existe. Verificando perks.")
        else:
            cursor.execute('''
                INSERT INTO survivors (name, gender, origin, role, dlc)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id;
            ''', (survivor_data['name'], survivor_data['gender'], survivor_data['origin'],
                  survivor_data['role'], survivor_data['dlc']))

            survivor_id = cursor.fetchone()[0]
            print(f"Sobrevivente '{survivor_data['name']}' inserido com sucesso!")

        for perk in survivor_data['perks']:
            cursor.execute("SELECT id FROM perks WHERE character_id = %s AND character_type = %s AND name = %s",
                           (survivor_id, 'survivor', perk['name']))
            existing_perk = cursor.fetchone()
            if not existing_perk:
                cursor.execute('''
                    INSERT INTO perks (character_id, character_type, name, description, icon_url)
                    VALUES (%s, %s, %s, %s, %s);
                ''', (survivor_id, 'survivor', perk['name'], perk['description'], perk['icon']))

        conn.commit()
        return survivor_id

    except Exception as e:
        conn.rollback()
        print(f"Erro ao inserir/atualizar dados do sobrevivente '{survivor_data['name']}': {e}")
        return None
    finally:
        if cursor: cursor.close()
        if conn: conn.close()


def main():
    # Substitua pela sua string de conexão real do Supabase
    global SUPABASE_CONNECTION_STRING
    SUPABASE_CONNECTION_STRING = "postgresql://postgres:123yahoo.V@db.oenlsdseisvusnvanxve.supabase.co:5432/postgres"

    setup_database()  # Configura as tabelas no Supabase

    print("\n--- INICIANDO RASPAR E INSERIR TODOS OS DADOS ---")

    # Raspagem e inserção de ASSASSINOS
    all_killers = killers_scrap()
    print(f"Raspados {len(all_killers)} assassinos. Iniciando inserção no DB...")
    for killer_data in all_killers:
        insert_killer_data(killer_data)
    print("Inserção de assassinos no DB concluída.")

    # Raspagem e inserção de SOBREVIVENTES
    all_survivors = survivor_scrap()
    print(f"Raspados {len(all_survivors)} sobreviventes. Iniciando inserção no DB...")
    for survivor_data in all_survivors:
        insert_survivor_data(survivor_data)
    print("Inserção de sobreviventes no DB concluída.")

    print("\n--- Exemplo de Leitura do Banco de Dados Supabase ---")
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            print("\nAssassinos (primeiros 5):")
            cursor.execute("SELECT id, nickname, real_name, dlc FROM killers LIMIT 5;")
            for row in cursor.fetchall():
                print(row)

            print("\nSobreviventes (primeiros 5):")
            cursor.execute("SELECT id, name, gender, dlc FROM survivors LIMIT 5;")
            for row in cursor.fetchall():
                print(row)

            print("\nPerks de assassinos (primeiras 5):")
            cursor.execute(
                "SELECT k.nickname, p.name, p.description FROM perks p JOIN killers k ON p.character_id = k.id WHERE p.character_type = 'killer' LIMIT 5;")
            for row in cursor.fetchall():
                print(f"  {row[0]}: {row[1]} - {row[2][:50]}...")

            print("\nPerks de sobreviventes (primeiras 5):")
            cursor.execute(
                "SELECT s.name, p.name, p.description FROM perks p JOIN survivors s ON p.character_id = s.id WHERE p.character_type = 'survivor' LIMIT 5;")
            for row in cursor.fetchall():
                print(f"  {row[0]}: {row[1]} - {row[2][:50]}...")

        except Exception as e:
            print(f"Erro ao ler do banco de dados: {e}")
        finally:
            if cursor: cursor.close()
            if conn: conn.close()
    else:
        print("Não foi possível conectar ao banco de dados para leitura.")


if __name__ == '__main__':
    main()

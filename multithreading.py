import requests
import time
import csv
import random
import concurrent.futures
from bs4 import BeautifulSoup
import os
from datetime import datetime

# global headers to be used for requests
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246'}

MAX_THREADS = 20

def extract_movie_details(movie_link, csv_filename):
    time.sleep(random.uniform(0, 0.2))
    try:
        response = requests.get(movie_link, headers=headers)
        movie_soup = BeautifulSoup(response.content, 'html.parser')

        if movie_soup is not None:
            title = None
            date = None
            rating = None
            plot_text = None
            votes = None
            duration = None
            genres = None
            director = None
            stars = None
            
            # Encontrando a seção específica
            page_section = movie_soup.find('section', attrs={'class': 'ipc-page-section'})
            
            if page_section is not None:
                # Encontrando todas as divs dentro da seção
                divs = page_section.find_all('div', recursive=False)
                
                if len(divs) > 1:
                    target_div = divs[1]
                    
                    # Encontrando o título do filme
                    title_tag = target_div.find('h1')
                    if title_tag:
                        title_span = title_tag.find('span')
                        if title_span:
                            title = title_span.get_text()
                    
                    # Encontrando a data de lançamento
                    date_tag = target_div.find('a', href=lambda href: href and 'releaseinfo' in href)
                    if date_tag:
                        date = date_tag.get_text().strip()
                    
                    # Encontrando a classificação do filme
                    rating_tag = movie_soup.find('div', attrs={'data-testid': 'hero-rating-bar__aggregate-rating__score'})
                    if rating_tag:
                        rating = rating_tag.get_text().strip().split('/')[0] if '/' in rating_tag.get_text() else rating_tag.get_text().strip()
                    
                    # Encontrando o número de votos
                    votes_tag = movie_soup.find('div', attrs={'data-testid': 'hero-rating-bar__aggregate-rating__score'})
                    if votes_tag:
                        votes_parent = votes_tag.find_parent()
                        if votes_parent:
                            votes_div = votes_parent.find('div', class_='sc-d541859f-3')
                            if votes_div:
                                votes = votes_div.get_text().strip()
                    
                    # Encontrando a sinopse do filme
                    plot_tag = movie_soup.find('span', attrs={'data-testid': 'plot-xs_to_m'})
                    if plot_tag:
                        plot_text = plot_tag.get_text().strip()
                    
                    # Encontrando duração
                    duration_tags = target_div.find_all('li', attrs={'class': 'ipc-inline-list__item'})
                    for tag in duration_tags:
                        text = tag.get_text()
                        if 'h' in text or 'm' in text:
                            duration = text.strip()
                            break
                    
                    # Encontrando gêneros
                    genre_tags = movie_soup.find_all('a', attrs={'class': 'ipc-chip'})
                    if genre_tags:
                        genres = ', '.join([tag.get_text().strip() for tag in genre_tags[:5]])
                    
                    # Encontrando diretor e elenco
                    cast_section = movie_soup.find('section', attrs={'data-testid': 'title-cast'})
                    if cast_section:
                        # Procurando pelo diretor
                        director_link = movie_soup.find('a', href=lambda href: href and '/name/' in href)
                        if director_link:
                            director = director_link.get_text().strip()
                    
                    # Encontrando principais atores
                    stars_section = movie_soup.find('div', attrs={'data-testid': 'title-pc-principal-credit'})
                    if stars_section:
                        star_links = stars_section.find_all('a', attrs={'class': 'ipc-metadata-list-item__list-content-item'})
                        if star_links:
                            stars = ', '.join([link.get_text().strip() for link in star_links[:3]])
                    
                    with open(csv_filename, mode='a', newline='', encoding='utf-8') as file:
                        movie_writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                        if title:
                            print(f"Extraindo: {title} - {date} - {rating}")
                            movie_writer.writerow([title, date, rating, votes, duration, genres, plot_text, director, stars, movie_link])
    except Exception as e:
        print(f"Erro ao extrair {movie_link}: {str(e)}")

def extract_movies(soup, csv_filename):
    movies_table = soup.find('div', attrs={'data-testid': 'chart-layout-main-column'})
    if not movies_table:
        print(f"Não foi possível encontrar a tabela de filmes para {csv_filename}")
        return
    
    movies_list = movies_table.find('ul')
    if not movies_list:
        print(f"Não foi possível encontrar a lista de filmes para {csv_filename}")
        return
    
    movies_table_rows = movies_list.find_all('li')
    movie_links = []
    
    for movie in movies_table_rows:
        link_tag = movie.find('a')
        if link_tag and link_tag.get('href'):
            movie_links.append('https://imdb.com' + link_tag['href'])
    
    print(f"\nEncontrados {len(movie_links)} filmes para processar em {csv_filename}")
    
    threads = min(MAX_THREADS, len(movie_links))
    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        executor.map(lambda link: extract_movie_details(link, csv_filename), movie_links)

def create_csv_with_header(filename):
    """Cria um arquivo CSV com cabeçalho"""
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['Título', 'Data de Lançamento', 'Avaliação', 'Votos', 'Duração', 'Gêneros', 'Sinopse', 'Diretor', 'Elenco Principal', 'Link'])

def scrape_category(url, filename, category_name):
    """Faz scraping de uma categoria específica"""
    print(f"\n{'='*60}")
    print(f"Iniciando extração: {category_name}")
    print(f"URL: {url}")
    print(f"Arquivo: {filename}")
    print(f"{'='*60}")
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        create_csv_with_header(filename)
        extract_movies(soup, filename)
        
        print(f"\n✓ Extração concluída para {category_name}!")
    except Exception as e:
        print(f"\n✗ Erro ao processar {category_name}: {str(e)}")

def main():
    start_time = time.time()
    
    print("\n" + "="*60)
    print("INICIANDO EXTRAÇÃO DE DADOS DE FILMES DO IMDB")
    print(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Criar pasta para os CSVs se não existir
    output_dir = 'dados_filmes'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Lista de categorias do IMDB para extrair
    categories = [
        {
            'name': 'Filmes Mais Populares',
            'url': 'https://www.imdb.com/chart/moviemeter/?ref_=nv_mv_mpm',
            'filename': os.path.join(output_dir, '01_filmes_mais_populares.csv')
        },
        {
            'name': 'Top 250 Melhores Filmes',
            'url': 'https://www.imdb.com/chart/top/?ref_=nv_mv_250',
            'filename': os.path.join(output_dir, '02_top_250_melhores_filmes.csv')
        },
        {
            'name': 'Filmes Mais Bem Avaliados',
            'url': 'https://www.imdb.com/chart/top/?ref_=nv_mv_250',
            'filename': os.path.join(output_dir, '03_filmes_mais_bem_avaliados.csv')
        },
        {
            'name': 'Filmes com Menor Avaliação',
            'url': 'https://www.imdb.com/chart/bottom/?ref_=nv_mv_bottom',
            'filename': os.path.join(output_dir, '04_filmes_pior_avaliados.csv')
        }
    ]
    
    # Processar cada categoria
    for category in categories:
        scrape_category(category['url'], category['filename'], category['name'])
        time.sleep(2)  # Pausa entre categorias para não sobrecarregar o servidor
    
    end_time = time.time()
    
    print("\n" + "="*60)
    print("EXTRAÇÃO FINALIZADA COM SUCESSO!")
    print(f"Tempo total: {end_time - start_time:.2f} segundos")
    print(f"Arquivos gerados na pasta: {output_dir}")
    print("="*60 + "\n")

if __name__ == '__main__':
    main()

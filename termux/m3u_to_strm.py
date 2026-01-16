#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
M3U to STRM Converter - Versão para Termux/Android
Gerador automático de arquivos .strm a partir de lista M3U para Emby

Autor: Assistente IA
Data: 2026-01-15
"""

import os
import re
import json
import hashlib
import requests
import unicodedata
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# =============================================================================
# CONFIGURAÇÕES - ALTERE CONFORME NECESSÁRIO
# =============================================================================

# URL da lista M3U (lida a partir do arquivo config.json ou usa padrão)
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")

# Pastas de destino no celular Android
PATHS = {
    "canais": "/storage/emulated/0/Emby/canais",
    "filmes": "/storage/emulated/0/Emby/filmes.strm",  # Nota: parece ser uma pasta, não arquivo
    "series": "/storage/emulated/0/Emby/series"
}

# Prefixos de grupo para categorização
CATEGORY_MAPPING = {
    "canais": ["Canais |"],
    "filmes": ["Filmes |", "Filmes Dublados", "Filmes Legendados", "VOD |"],
    "series": ["Series |", "Novelas", "Animes |"]
}

# Grupos para ignorar (conteúdo adulto)
IGNORE_GROUPS = [
    "Adult", "Adulto", "XXX", "+18", "18+", 
    "Canais | Adultos", "Filmes | Adultos"
]

# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def load_config() -> Dict:
    """Carrega configurações do arquivo JSON"""
    default_config = {
        "m3u_url": "",
        "paths": PATHS,
        "last_sync": None,
        "processed_items": {}
    }
    
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Merge com defaults
                for key in default_config:
                    if key not in config:
                        config[key] = default_config[key]
                return config
        except Exception as e:
            print(f"⚠️ Erro ao carregar config: {e}")
    
    return default_config


def save_config(config: Dict):
    """Salva configurações no arquivo JSON"""
    try:
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Erro ao salvar config: {e}")


def sanitize_filename(name: str) -> str:
    """Remove caracteres inválidos do nome do arquivo"""
    # Normaliza caracteres Unicode
    name = unicodedata.normalize('NFKD', name)
    # Remove caracteres inválidos para nomes de arquivo
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '')
    # Remove pontos consecutivos (Windows não aceita)
    while '..' in name:
        name = name.replace('..', '.')
    # Remove ponto no final (Windows não aceita)
    name = name.rstrip('.')
    # Remove espaços extras
    name = ' '.join(name.split())
    # Limita tamanho
    if len(name) > 200:
        name = name[:200]
    # Garante que não está vazio
    if not name:
        name = "sem_nome"
    return name.strip()


def get_item_hash(name: str, url: str) -> str:
    """Gera hash único para um item"""
    content = f"{name}|{url}"
    return hashlib.md5(content.encode()).hexdigest()[:16]


def categorize_item(group_title: str) -> Optional[str]:
    """Determina a categoria do item baseado no grupo"""
    group_lower = group_title.lower()
    
    # Verifica se deve ignorar
    for ignore in IGNORE_GROUPS:
        if ignore.lower() in group_lower:
            return None
    
    # Categoriza
    for category, prefixes in CATEGORY_MAPPING.items():
        for prefix in prefixes:
            if group_title.startswith(prefix) or prefix.lower() in group_lower:
                return category
    
    return None


def parse_extinf_line(line: str) -> Dict:
    """Faz parse de uma linha EXTINF"""
    result = {
        "tvg_name": "",
        "tvg_logo": "",
        "group_title": "",
        "display_name": ""
    }
    
    # Extrai tvg-name
    tvg_name_match = re.search(r'tvg-name="([^"]*)"', line)
    if tvg_name_match:
        result["tvg_name"] = tvg_name_match.group(1)
    
    # Extrai tvg-logo
    tvg_logo_match = re.search(r'tvg-logo="([^"]*)"', line)
    if tvg_logo_match:
        result["tvg_logo"] = tvg_logo_match.group(1)
    
    # Extrai group-title
    group_match = re.search(r'group-title="([^"]*)"', line)
    if group_match:
        result["group_title"] = group_match.group(1)
    
    # Extrai nome de exibição (último vírgula)
    parts = line.split(',')
    if len(parts) > 1:
        result["display_name"] = parts[-1].strip()
    
    return result


def load_m3u(source: str) -> Optional[str]:
    """Carrega lista M3U de arquivo local ou URL"""
    
    # Verifica se é arquivo local
    if os.path.exists(source):
        print(f"� Lendo arquivo local: {source}")
        try:
            with open(source, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            print(f"✅ Arquivo carregado! ({len(content):,} caracteres)")
            return content
        except Exception as e:
            print(f"❌ Erro ao ler arquivo: {e}")
            return None
    
    # Senão, tenta baixar da URL
    print(f"📥 Baixando lista M3U de: {source[:50]}...")
    
    headers = {
        'User-Agent': 'VLC/3.0.12 LibVLC/3.0.12'
    }
    
    try:
        response = requests.get(source, timeout=120, headers=headers)
        response.raise_for_status()
        
        content = response.text
        print(f"✅ Download concluído! ({len(content):,} caracteres)")
        return content
    except requests.RequestException as e:
        print(f"❌ Erro ao baixar M3U: {e}")
        return None


def parse_m3u_content(content: str) -> List[Dict]:
    """Faz parse do conteúdo M3U e retorna lista de itens"""
    items = []
    lines = content.split('\n')
    
    print(f"📊 Processando {len(lines):,} linhas...")
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if line.startswith('#EXTINF:'):
            info = parse_extinf_line(line)
            
            # Próxima linha deve ser a URL
            if i + 1 < len(lines):
                url = lines[i + 1].strip()
                if url and not url.startswith('#'):
                    category = categorize_item(info["group_title"])
                    
                    if category:  # Apenas se tiver categoria válida
                        items.append({
                            "name": info["tvg_name"] or info["display_name"],
                            "display_name": info["display_name"],
                            "group": info["group_title"],
                            "url": url,
                            "logo": info["tvg_logo"],
                            "category": category,
                            "hash": get_item_hash(info["tvg_name"], url)
                        })
                    i += 1
        i += 1
    
    print(f"✅ Encontrados {len(items):,} itens válidos")
    return items


def organize_series(items: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Organiza séries em pastas por nome da série
    Detecta padrões como "Nome S01E01" ou "Nome S01E01"
    """
    series_dict = {}
    episode_pattern = re.compile(r'(.+?)\s*S(\d+)E(\d+)', re.IGNORECASE)
    
    for item in items:
        if item["category"] == "series":
            match = episode_pattern.match(item["name"])
            if match:
                series_name = match.group(1).strip()
                season = int(match.group(2))
                episode = int(match.group(3))
                
                if series_name not in series_dict:
                    series_dict[series_name] = []
                
                series_dict[series_name].append({
                    **item,
                    "series_name": series_name,
                    "season": season,
                    "episode": episode
                })
    
    return series_dict


def create_strm_file(filepath: str, url: str) -> bool:
    """Cria um arquivo .strm com a URL do stream"""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(url)
        return True
    except Exception as e:
        print(f"❌ Erro ao criar {filepath}: {e}")
        return False


def generate_strm_files(items: List[Dict], config: Dict) -> Tuple[int, int, int]:
    """Gera arquivos .strm para todos os itens"""
    paths = config.get("paths", PATHS)
    processed = config.get("processed_items", {})
    
    created = 0
    skipped = 0
    errors = 0
    
    # Organiza séries por nome
    series_organized = organize_series([i for i in items if i["category"] == "series"])
    
    for item in items:
        try:
            category = item["category"]
            base_path = paths.get(category)
            
            if not base_path:
                skipped += 1
                continue
            
            # Define caminho do arquivo (movido para antes do check de cache para conferir se o arquivo ainda existe no disco)
            if category == "series":
                # Organiza em pasta da série/temporada
                match = re.match(r'(.+?)\s*S(\d+)E(\d+)', item["name"], re.IGNORECASE)
                if match:
                    series_name = sanitize_filename(match.group(1))
                    season = int(match.group(2))
                    episode_name = sanitize_filename(item["display_name"])
                    
                    # Cria estrutura série/temporada/episódio
                    filepath = os.path.join(
                        base_path,
                        series_name,
                        f"Season {season:02d}",
                        f"{episode_name}.strm"
                    )
                else:
                    filepath = os.path.join(
                        base_path,
                        sanitize_filename(item["group"].replace("Series | ", "")),
                        f"{sanitize_filename(item['name'])}.strm"
                    )
            
            elif category == "canais":
                # Organiza canais em subpastas por subcategoria
                subcategory = item["group"].replace("Canais | ", "")
                filepath = os.path.join(
                    base_path,
                    sanitize_filename(subcategory),
                    f"{sanitize_filename(item['name'])}.strm"
                )
            
            elif category == "filmes":
                # Filmes direto na pasta
                filepath = os.path.join(
                    base_path,
                    f"{sanitize_filename(item['name'])}.strm"
                )
            
            else:
                filepath = os.path.join(
                    base_path,
                    f"{sanitize_filename(item['name'])}.strm"
                )

            # Verifica se já foi processado E se o arquivo ainda existe no disco
            if item["hash"] in processed and os.path.exists(filepath):
                skipped += 1
                continue
            
            # Cria arquivo .strm
            if create_strm_file(filepath, item["url"]):
                processed[item["hash"]] = {
                    "name": item["name"],
                    "created_at": datetime.now().isoformat(),
                    "path": filepath
                }
                created += 1
            else:
                errors += 1
                
        except Exception as e:
            print(f"❌ Erro processando {item.get('name', 'desconhecido')}: {e}")
            errors += 1
    
    # Atualiza config com itens processados
    config["processed_items"] = processed
    config["last_sync"] = datetime.now().isoformat()
    
    return created, skipped, errors


def print_summary(items: List[Dict]):
    """Imprime resumo dos itens encontrados"""
    categories = {}
    groups = {}
    
    for item in items:
        cat = item["category"]
        grp = item["group"]
        
        categories[cat] = categories.get(cat, 0) + 1
        groups[grp] = groups.get(grp, 0) + 1
    
    print("\n📊 RESUMO DOS ITENS:")
    print("-" * 40)
    
    print("\n📁 Por Categoria:")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"   {cat}: {count:,}")
    
    print(f"\n📺 Total de grupos: {len(groups)}")


# =============================================================================
# FUNÇÃO PRINCIPAL
# =============================================================================

def main():
    """Função principal do script"""
    print("=" * 60)
    print("🎬 M3U to STRM Converter - Termux Edition")
    print("📱 Gerador automático de arquivos .strm para Emby")
    print("=" * 60)
    print()
    
    # Carrega configurações
    config = load_config()
    
    # Verifica fonte do M3U (arquivo local ou URL)
    m3u_source = config.get("m3u_file") or config.get("m3u_url")
    if not m3u_source:
        print("⚠️ Fonte do M3U não configurada!")
        print("📝 Configure no arquivo config.json ou informe agora:")
        print("   (pode ser URL ou caminho de arquivo local)")
        m3u_source = input("URL ou arquivo M3U: ").strip()
        
        if not m3u_source:
            print("❌ Fonte inválida. Saindo...")
            return
        
        if os.path.exists(m3u_source):
            config["m3u_file"] = m3u_source
        else:
            config["m3u_url"] = m3u_source
        save_config(config)
    
    print(f"\n📅 Última sincronização: {config.get('last_sync', 'Nunca')}")
    print(f"📊 Itens já processados: {len(config.get('processed_items', {})):,}")
    
    # Carrega lista M3U (arquivo ou URL)
    print()
    m3u_content = load_m3u(m3u_source)
    if not m3u_content:
        return
    
    # Faz parse do conteúdo
    items = parse_m3u_content(m3u_content)
    print_summary(items)
    
    # Gera arquivos .strm
    print("\n🔄 Gerando arquivos .strm...")
    created, skipped, errors = generate_strm_files(items, config)
    
    # Salva configurações atualizadas
    save_config(config)
    
    # Resumo final
    print("\n" + "=" * 60)
    print("✅ PROCESSO CONCLUÍDO!")
    print("=" * 60)
    print(f"   📁 Novos arquivos criados: {created:,}")
    print(f"   ⏭️  Itens ignorados/existentes: {skipped:,}")
    print(f"   ❌ Erros: {errors}")
    print(f"   📅 Última sync: {config.get('last_sync')}")
    print()


if __name__ == "__main__":
    main()

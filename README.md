# 🎬 M3U to STRM Converter (Android/Termux Edition)

Este projeto automatiza a geração de arquivos `.strm` a partir de listas IPTV M3U, permitindo que você integre canais, filmes e séries diretamente em servidores de mídia como o **Emby** no Android.

## 📱 Objetivo
Facilitar a organização de playlists IPTV gigantescas (como as de 70MB+ com mais de 500k linhas) que travam leitores convencionais, transformando-as em uma estrutura de arquivos leve que o Emby pode processar sem consumir memória excessiva.

## 🚀 Funcionalidades
- **Categorização Automática:** Separa Canais, Filmes e Séries.
- **Estruturação de Séries:** Identifica temporadas e episódios (S01E01) e organiza em pastas.
- **Otimizado para Celular:** Desenvolvido para rodar leve no Termux (Android) com baixo consumo de RAM.
- **Sincronização Inteligente:** Usa cache (Hashes) para processar apenas itens novos ou alterados.
- **Filtro Adulto:** Opção para ignorar grupos de conteúdo adulto automaticamente.

## 🛠️ Tecnologias
- **Python 3**
- **Termux** (Para execução em segundo plano no Android)
- **Emby Server Android**

## 📂 Estrutura do Projeto
- `termux/m3u_to_strm.py`: O núcleo do processamento.
- `termux/INSTRUCOES.md`: Guia passo a passo completo para instalação no Android.
- `termux/config.json.example`: Modelo de configuração.

## 📖 Como Usar
Para instruções detalhadas de como configurar no seu celular, siga o guia em:
👉 **[Instruções de Instalação e Uso (Termux)](termux/INSTRUCOES.md)**

## 📧 Contato
Desenvolvido para uso pessoal e automatização residencial.
Autor: pedrabrancagames@gmail.com

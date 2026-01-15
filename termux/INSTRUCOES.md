# 📱 Guia de Instalação - M3U to STRM para Termux

Este sistema automatiza a geração de arquivos `.strm` a partir da sua lista IPTV M3U, salvando diretamente nas pastas do Emby no seu Samsung S20 FE.

## 📋 Pré-requisitos

- Samsung S20 FE (ou qualquer Android)
- Aplicativo **Termux** instalado (via F-Droid, não Play Store!)
- Emby Server rodando no celular

---

## 🔧 Instalação Passo a Passo

### 1️⃣ Instalar Termux

1. Baixe o **F-Droid** (loja alternativa): https://f-droid.org/
2. No F-Droid, busque e instale **Termux**
3. Abra o Termux

### 2️⃣ Configurar Termux

Execute os seguintes comandos no Termux:

```bash
# Atualiza pacotes
pkg update && pkg upgrade -y

# Instala Python e dependências
pkg install python -y
pkg install git -y

# Concede permissão de armazenamento
termux-setup-storage
```

**⚠️ IMPORTANTE**: Quando aparecer o popup pedindo permissão de armazenamento, **ACEITE**!

### 3️⃣ Instalar Bibliotecas Python

```bash
pip install requests
```

### 4️⃣ Copiar Arquivos do Script

Você tem duas opções:

**Opção A - Via USB/Computador:**
1. Conecte o celular ao PC
2. Copie a pasta `termux` para: `/storage/emulated/0/Download/m3u_strm/`

**Opção B - Baixar diretamente no Termux:**
```bash
# Cria pasta do projeto
mkdir -p ~/m3u_strm
cd ~/m3u_strm

# Copia do storage interno (se você copiou via USB)
cp /storage/emulated/0/Download/m3u_strm/* ~/m3u_strm/
```

### 5️⃣ Configurar o Script

Edite o arquivo `config.json`:

```bash
cd ~/m3u_strm
nano config.json
```

Altere conforme necessário:
- `m3u_url`: URL da sua lista IPTV
- `m3u_file`: Caminho do arquivo M3U local (alternativa à URL)
- `paths`: Pastas do Emby no celular

**Exemplo de config.json:**
```json
{
  "m3u_url": "http://sua_lista.com/get.php?...",
  "m3u_file": "",
  "paths": {
    "canais": "/storage/emulated/0/Emby/canais",
    "filmes": "/storage/emulated/0/Emby/filmes.strm",
    "series": "/storage/emulated/0/Emby/series"
  }
}
```

Para salvar no nano: `Ctrl+O`, Enter, `Ctrl+X`

---

## 🚀 Executando o Script

### Execução Manual

```bash
cd ~/m3u_strm
python m3u_to_strm.py
```

### Usando Arquivo M3U Local

Se você já tem o arquivo M3U no celular:

```bash
# Copia o arquivo M3U para a pasta do projeto
cp /storage/emulated/0/Download/sua_lista.m3u ~/m3u_strm/

# Edita config para usar arquivo local
nano config.json
# Preencha: "m3u_file": "/data/data/com.termux/files/home/m3u_strm/sua_lista.m3u"
```

---

## ⏰ Agendamento Automático (Executar Diariamente)

### Instalar cron no Termux

```bash
pkg install cronie -y
```

### Configurar agendamento

```bash
# Abre editor de crontab
crontab -e
```

Adicione a linha (executa às 3h da manhã):
```
0 3 * * * cd /data/data/com.termux/files/home/m3u_strm && python m3u_to_strm.py >> sync.log 2>&1
```

Para salvar: `Ctrl+O`, Enter, `Ctrl+X`

### Iniciar serviço cron

```bash
crond
```

Para iniciar automaticamente quando o Termux abrir:
```bash
echo "crond" >> ~/.bashrc
```

---

## 🔍 Verificando Resultados

Após executar, verifique as pastas do Emby:

```bash
# Lista canais criados
ls /storage/emulated/0/Emby/canais/

# Lista séries criadas
ls /storage/emulated/0/Emby/series/

# Conta arquivos .strm
find /storage/emulated/0/Emby -name "*.strm" | wc -l
```

---

## 🐛 Solução de Problemas

### "Permission denied"
```bash
termux-setup-storage
# Aceite a permissão no popup
```

### "No module named requests"
```bash
pip install requests
```

### Script não encontra o arquivo M3U
- Use caminho absoluto no config.json
- Verifique se o arquivo existe: `ls -la /caminho/do/arquivo.m3u`

### Emby não reconhece os arquivos .strm
1. No Emby, vá em **Configurações > Biblioteca**
2. Adicione as pastas criadas como bibliotecas
3. Force uma **Atualização da Biblioteca**

---

## 📁 Estrutura de Pastas Criadas

```
/storage/emulated/0/Emby/
├── canais/
│   ├── 4K [FHDR]/
│   │   ├── A&E 4K FHDR.strm
│   │   └── ...
│   ├── Variedades/
│   ├── Esportes/
│   └── ...
├── filmes.strm/
│   ├── Filme 1.strm
│   └── ...
└── series/
    ├── Nome da Serie/
    │   ├── Season 01/
    │   │   ├── Nome da Serie S01E01.strm
    │   │   └── ...
    │   └── Season 02/
    └── ...
```

---

## 💡 Dicas

1. **Execute de madrugada**: O agendamento às 3h evita interferir no uso
2. **Mantenha o Termux ativo**: Use o app "Termux:Boot" para iniciar automaticamente
3. **Backup do config.json**: Salve uma cópia do arquivo de configuração
4. **Logs**: O arquivo `sync.log` contém o histórico de execuções

---

## 📞 Comandos Úteis

```bash
# Ver último log de sincronização
cat ~/m3u_strm/sync.log | tail -50

# Forçar resincronização completa (limpa cache)
rm ~/m3u_strm/config.json
python m3u_to_strm.py

# Ver espaço usado pelos .strm
du -sh /storage/emulated/0/Emby/

# Contar itens por categoria
find /storage/emulated/0/Emby/canais -name "*.strm" | wc -l
find /storage/emulated/0/Emby/series -name "*.strm" | wc -l
```

---

**Pronto!** Agora seu sistema Emby será atualizado automaticamente quando houver novos filmes, séries ou canais na lista IPTV! 🎉

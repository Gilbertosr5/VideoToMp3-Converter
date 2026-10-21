# AudioLocal — YouTube to MP3 Converter

**English version below.**

Um conversor local de áudio desenvolvido em Python que permite extrair e converter áudio de vídeos e links compatíveis para MP3, diretamente pelo navegador.

O projeto foi criado para uso pessoal, com uma interface web simples e processamento executado na própria máquina.

## ✨ Funcionalidades

- Conversão de links compatíveis para MP3.
- Seleção de qualidade do áudio: 128, 192 ou 320 kbps.
- Acompanhamento do progresso do download e da conversão.
- Histórico de conversões com SQLite.
- Download dos arquivos MP3 pelo navegador.
- Execução local, sem necessidade de hospedar o backend em um servidor externo.

## 🛠️ Tecnologias

- **Python** — linguagem principal.
- **Flask** — aplicação web e API local.
- **yt-dlp** — extração de mídia de fontes compatíveis.
- **FFmpeg** — processamento e conversão de áudio.
- **SQLite** — armazenamento do histórico.
- **HTML, CSS e JavaScript** — interface web.

## 🚀 Como executar

### Pré-requisitos

- Python instalado.
- Conexão com a internet para obter mídias de fontes online.

### Instalação

Clone o repositório e acesse a pasta do projeto:

```bash
git clone <REPOSITORY_URL>
cd AudioLocal
```

Crie e ative um ambiente virtual:

**Windows (PowerShell)**

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Instale as dependências:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Inicie a aplicação:

```bash
python app.py
```

Abra no navegador:

http://127.0.0.1:5000

Mantenha o terminal aberto enquanto estiver utilizando o conversor.

## 📁 Estrutura do projeto

```text
AudioLocal/
├── app.py
├── requirements.txt
├── history.sqlite3
├── downloads/
├── templates/
│   └── index.html
└── static/
    ├── app.js
    └── style.css
```

O banco de dados e os arquivos baixados são gerados localmente durante o uso.

## ⚠️ Observações

- A aplicação foi projetada para execução local e não deve ser exposta diretamente à internet sem medidas adicionais de segurança.
- A compatibilidade depende da fonte e do suporte do `yt-dlp`.
- Utilize o projeto somente com conteúdos que você tenha autorização para baixar e converter, respeitando os direitos autorais e os termos de uso das plataformas.

---

# AudioLocal — YouTube to MP3 Converter

A local audio converter built with Python that extracts and converts audio from compatible videos and links into MP3 files directly through a web browser.

The project was designed for personal use, with a simple web interface and processing performed on the user's own machine.

## ✨ Features

- Convert compatible media links to MP3.
- Choose audio quality: 128, 192, or 320 kbps.
- Track download and conversion progress.
- Store conversion history using SQLite.
- Download converted MP3 files through the browser.
- Run locally without hosting the backend on an external server.

## 🛠️ Technologies

- **Python** — core programming language.
- **Flask** — local web application and API.
- **yt-dlp** — media extraction from supported sources.
- **FFmpeg** — audio processing and conversion.
- **SQLite** — conversion history storage.
- **HTML, CSS, and JavaScript** — web interface.

## 🚀 Getting Started

### Prerequisites

- Python installed.
- An internet connection to retrieve media from online sources.

### Installation

Clone the repository and navigate to the project directory:

```bash
git clone <REPOSITORY_URL>
cd AudioLocal
```

Create and activate a virtual environment:

**Windows (PowerShell)**

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the dependencies:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Start the application:

```bash
python app.py
```

Open the following address in your browser:

http://127.0.0.1:5000

Keep the terminal open while using the converter.

## 📁 Project Structure

```text
AudioLocal/
├── app.py
├── requirements.txt
├── history.sqlite3
├── downloads/
├── templates/
│   └── index.html
└── static/
    ├── app.js
    └── style.css
```

The database and downloaded files are generated locally during use.

## ⚠️ Notes

- The application is designed for local use and should not be exposed directly to the internet without additional security measures.
- Compatibility depends on the source and the support provided by `yt-dlp`.
- Only download and convert content you are authorized to use, in compliance with copyright laws and platform terms of service.

---

## 📄 License

Add a `LICENSE` file to specify how others may use, modify, and distribute this project.

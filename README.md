# SPARQL-MCP-Kel-2

Mengembangkan sistem analisis keamanan berbasis Agentic AI menggunakan SPARQL-MCP dan Cybersecurity Knowledge Graphs.

## Deskripsi

Proyek ini mengimplementasikan sistem agentic AI untuk analisis keamanan siber yang mengintegrasikan Large Language Model (LLM) dengan Cybersecurity Knowledge Graph (CSKG) melalui framework SPARQL-MCP. Sistem ini memungkinkan query berbasis bahasa natural atas basis pengetahuan keamanan terstruktur, pembuatan query SPARQL secara otomatis, serta penalaran multi-agent untuk analisis ancaman dan kerentanan.

Antarmuka chatbot/pencarian terinspirasi dari [WU Search AI](https://search.ai.wu.ac.at/), dan basis knowledge graph menggunakan dataset [SEPSES CSKG](https://sepses.ifs.tuwien.ac.at/).

## Dokumentasi

Saat ini repository ini berisi modul **SPARQL-MCP Server** yang tersimpan di `main/sparqlmcp-main/`. Dokumentasi lengkap (setup, konfigurasi `.env`, dan cara menjalankan server) tersedia di:

- `main/sparqlmcp-main/README.md`

## Struktur Folder (Saat Ini)

```
.
├─ LICENSE
├─ README.md
└─ main/
	└─ sparqlmcp-main/
		├─ .env.example
		├─ .gitignore
		├─ pyproject.toml
		├─ README.md
		├─ requirements.txt
		├─ src/
			└─ sparql_mcp_server/
				├─ __init__.py
				├─ handlers.py
				├─ server.py
				└─ web.py
		├─ frontend/
			├─ .vscode/
			├─ public/
			└─ src/
		└─ database/
			└─ seed data/
				├─graph0000001_cpe.ttl.gz
				├─graph0000001_cve.ttl.gz
				└─graph000001_cwe.ttl.gz
```

## Anggota Kelompok

| Nama                             | NIM                | GitHub                                     | Role                  |
| -------------------------------- | ------------------ | ------------------------------------------ | --------------------- |
| Arnoldus Dharma Wasesa Mahasmara | 24/545535/PA/23182 | [@Arnold-XV](https://github.com/Arnold-XV) | Agent Developer (PIC) |
| Hafidz Kurniawan Nahruntoko      | 24/539859/PA/22920 | [@DaisyDazy](https://github.com/DaisyDazy) | Data Engineer         |
| Adzrha Auryn Alius               | 24/533582/PA/22594 | [@teksarin](https://github.com/teksarin)   | Web Developer         |
| Jessy Marcia Anabel              | 24/538431/PA/22846 | [@jsmarciaa](https://github.com/jsmarciaa) | Quality Assurance     |

## Setup Triplestore

1. Cek apakah Java sudah terinstal di perangkat dengan `java --version` di terminal
2. Install fuseki dengan format `apache-jena-fuseku-6.x.x.zip` pada laman [jena.apache.org/download/](https://jena.apache.org/download/)
3. Ekstrak file zip
4. Cari file bernama `fuseki-server.bat` dan jalankan
5. Pergi ke laman [localhost:3030](http://localhost:3030/sepses/query)
6. Unduh dataset yang ada pada Repositori ini pada `main\sparqlmcp-main\database\seed data`
7. Ekstrak masing masing file .ttl
8. Upload data dengan klik `add data` pada laman apache jena fuseki

## Referensi

- Ekelhart, A. et al. (2019). SEPSES Knowledge Graph: An Integrated Resource for Cybersecurity. _ISWC 2019_. [Springer](https://link.springer.com/chapter/10.1007/978-3-030-30796-7_13)
- SEPSES CSKG SPARQL Endpoint and Vocabulary. [CEUR-WS Vol-4079](https://ceur-ws.org/Vol-4079/paper11.pdf)
- Ekelhart, A. et al. (2024). RAGE-KG: Retrieval-Augmented Generation with Enterprise Knowledge Graphs. [UniVie](https://eprints.cs.univie.ac.at/8178/)
- [SPARQL-MCP GitHub](https://github.com/semantisch/sparqlmcp)
- [WU Search AI](https://search.ai.wu.ac.at/)

Disclaimer: All rights, intellectual property, credits, and original licenses for the SPARQL-MCP framework belong entirely to the original creators (https://github.com/semantisch/sparqlmcp). This repository is solely for integrating their work into our project. We do not claim ownership of these specific framework files.

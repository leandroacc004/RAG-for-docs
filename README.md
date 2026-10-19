# RAG for docs

Haz preguntas a tus propios documentos desde la terminal. El programa parte los documentos en *chunks*, busca los más relevantes para tu pregunta y le pide a Claude que responda **solo** con esa información, citando de dónde sacó cada dato.

Es un RAG (*Retrieval-Augmented Generation*) mínimo, sin bases de datos ni servicios externos aparte de Claude, para que veas cada pieza por dentro.

## Cómo funciona

```
INGESTA (una vez)                         CONSULTA (cada pregunta)

docs/*.md ──► chunker ──► indice.json     pregunta ──► BM25 ──► top-k chunks ──► Claude ──► respuesta
              (800 car.,                                (palabras             (con ids)          con citas
               150 solape)                               clave)                                  [archivo#n]
```

1. **`ingest.py`** lee cada documento y lo parte con un *chunker recursivo*: intenta cortar por párrafos; si un párrafo es muy largo, baja a líneas, luego a oraciones, palabras y, como último recurso, caracteres. Así casi nunca se corta una frase a la mitad.
2. Cada chunk se guarda con un **id** (`politica_vacaciones.md#2`) y el **título** de su documento.
3. **`ask.py`** busca con **BM25**, el algoritmo clásico de búsqueda por palabras clave (el que usan Elasticsearch y Lucene).
4. Los mejores chunks se envían a Claude dentro de etiquetas `<fragmento id="...">`, con la pregunta al final. El *system prompt* le exige citar ids y admitir cuando la respuesta no está en los fragmentos.

## Conceptos clave

| Concepto | Dónde verlo | Qué probar |
|---|---|---|
| **Tamaño de chunk** | `ingest.py --tam` | Con `--tam 200` los chunks pierden contexto; con `--tam 3000` mandas texto irrelevante (más caro y con más ruido). |
| **Solapamiento** | `ingest.py --solape` | Pon `--solape 0` y busca una pregunta cuya respuesta caiga entre dos chunks. |
| **Top-k** | `ask.py --k` | Con `--k 1` puede faltar información; con `--k 9` mandas todo el corpus. |
| **Grounding** | `SYSTEM` en `ask.py` | Pregunta algo que no está en los documentos y fíjate que no invente. |
| **Contexto del chunk** | `armar_contexto()` | El título del documento viaja con cada chunk, para que un fragmento suelto como "son 15 días" tenga sentido. |

Usa `--ver` en la ingesta y `--ver-chunks` en las preguntas para ver exactamente qué texto se genera y qué se le envía a Claude.

## Estructura

| Archivo | Para qué sirve |
|---|---|
| `chunker.py` | Chunking recursivo con solapamiento |
| `bm25.py` | Búsqueda BM25 en Python puro, con normalización de tildes y plurales |
| `ingest.py` | Lee `docs/`, genera chunks y guarda `indice.json` |
| `ask.py` | Recupera chunks y consulta a Claude (modo pregunta única o interactivo) |
| `llm.py` | Cliente de Claude y manejo de rechazos o respuestas cortadas |
| `docs/` | Documentos de ejemplo de una empresa ficticia (Nimbus Software) |

## Instalación

Necesitas Python 3.10 o superior y una API key de Anthropic ([console.anthropic.com](https://console.anthropic.com)).

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY="tu-api-key"   # Windows: set ANTHROPIC_API_KEY=tu-api-key
```

## Uso

```bash
# 1. Crear el índice (vuelve a ejecutarlo cada vez que cambies los documentos)
python ingest.py

# 2. Preguntar
python ask.py "¿Cuántos días de vacaciones tengo?"
python ask.py "¿Puedo trabajar desde casa?" --ver-chunks

# Modo interactivo
python ask.py
```

Salida de ejemplo:

```
Fragmentos recuperados: politica_vacaciones.md#0 (1.65), politica_vacaciones.md#2 (1.63), ...

Tienes 15 días hábiles de vacaciones pagadas por año [politica_vacaciones.md#0]. Desde el tercer
año se suma un día por año, hasta un máximo de 20 [politica_vacaciones.md#0]...
```

Para usar tus documentos, ponlos en `docs/` (o usa `--docs otra/carpeta`) en formato `.md` o `.txt`.

## Configuración

| Variable | Valor por defecto | Descripción |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | Tu API key (obligatoria) |
| `CLAUDE_MODEL` | `claude-opus-5-5` | Modelo que redacta la respuesta |

## Limitaciones (a propósito)

BM25 solo encuentra **palabras que coinciden**. Si preguntas "¿cuánto me pagan por internet?" y el documento dice "bono mensual para gastos de internet", lo encuentra; pero si preguntas por "teletrabajo" y el documento dice "trabajo remoto", puede fallar. Ese es el problema que resuelven los **embeddings** (búsqueda semántica).

## Ideas para seguir aprendiendo

1. **Embeddings:** reemplaza o complementa BM25 con un modelo de embeddings (Anthropic recomienda [Voyage AI](https://docs.claude.com/en/docs/build-with-claude/embeddings)) y compara resultados.
2. **Búsqueda híbrida:** combina BM25 + embeddings con *Reciprocal Rank Fusion* (lo verás en el proyecto RAG multi-fuente).
3. **Chunking por estructura:** corta por encabezados `##` de Markdown en vez de por tamaño.
4. **Contextual Retrieval:** pide a Claude un resumen de una línea del documento y agrégalo a cada chunk antes de indexar ([artículo de Anthropic](https://www.anthropic.com/news/contextual-retrieval)).
5. **PDFs:** agrega soporte con `pypdf` en `ingest.py`.

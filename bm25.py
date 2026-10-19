"""Búsqueda por palabras clave con BM25, sin dependencias externas.

BM25 da más puntaje a un chunk cuando:
  - contiene las palabras de la pregunta muchas veces (con rendimientos decrecientes, k1),
  - esas palabras son raras en el resto de los chunks (IDF),
  - el chunk no es exageradamente largo (normalización por longitud, b).
Es el mismo algoritmo que usan Elasticsearch y Lucene por defecto.
"""

import math
import re
import unicodedata
from collections import Counter

STOPWORDS = set(
    "a al algo algunas algunos ante antes como con contra cual cuando de del desde donde durante e el ella "
    "ellas ellos en entre era es esa esas ese eso esos esta estas este esto estos fue ha hay la las le les lo "
    "los mas me mi mis muy ni no nos o os otra otro para pero poco por porque que quien se sea ser si sin "
    "sobre son su sus tambien te tiene tu tus un una unas uno unos y ya yo puedo puede cuanto cuantos cuantas".split()
)


def normalizar(palabra: str) -> str:
    """Minúsculas, sin tildes y con un 'stemming' muy simple para plurales."""
    palabra = unicodedata.normalize("NFD", palabra.lower())
    palabra = "".join(c for c in palabra if unicodedata.category(c) != "Mn")
    if len(palabra) > 4 and palabra.endswith("es"):
        palabra = palabra[:-2]
    elif len(palabra) > 3 and palabra.endswith("s"):
        palabra = palabra[:-1]
    return palabra


def tokenizar(texto: str) -> list[str]:
    tokens = (normalizar(p) for p in re.findall(r"\w+", texto))
    return [t for t in tokens if t not in STOPWORDS and len(t) > 1]


class BM25:
    def __init__(self, documentos: list[str], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.docs = [Counter(tokenizar(d)) for d in documentos]
        self.largos = [sum(c.values()) for c in self.docs]
        self.largo_medio = sum(self.largos) / max(len(self.docs), 1)
        n = len(self.docs)
        df = Counter(t for doc in self.docs for t in doc)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def puntuar(self, consulta: str) -> list[float]:
        terminos = tokenizar(consulta)
        puntajes = []
        for doc, largo in zip(self.docs, self.largos):
            s = 0.0
            for t in terminos:
                tf = doc.get(t, 0)
                if tf:
                    norm = self.k1 * (1 - self.b + self.b * largo / self.largo_medio)
                    s += self.idf[t] * tf * (self.k1 + 1) / (tf + norm)
            puntajes.append(s)
        return puntajes

    def buscar(self, consulta: str, k: int = 4) -> list[tuple[int, float]]:
        """Devuelve [(indice_del_chunk, puntaje)] de los k mejores, ignorando los que no coinciden en nada."""
        puntajes = self.puntuar(consulta)
        orden = sorted(range(len(puntajes)), key=lambda i: puntajes[i], reverse=True)
        return [(i, puntajes[i]) for i in orden[:k] if puntajes[i] > 0]

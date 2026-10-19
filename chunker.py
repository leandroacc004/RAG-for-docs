"""Chunking recursivo con solapamiento.

Idea: intentamos cortar el texto por los separadores más "naturales" primero
(párrafos), y solo si un pedazo sigue siendo muy grande bajamos a separadores
más finos (líneas, oraciones, palabras, caracteres). Así los chunks respetan
la estructura del texto en vez de cortar frases a la mitad.

El solapamiento (overlap) repite el final de un chunk al inicio del siguiente,
para que una idea que cae justo en el borde no se pierda.
"""

SEPARADORES = ["\n\n", "\n", ". ", " ", ""]


def unir(partes: list[str], sep: str, tam: int, solape: int) -> list[str]:
    """Junta partes pequeñas en chunks de hasta `tam` caracteres, con solapamiento."""
    chunks: list[str] = []
    actual: list[str] = []
    for parte in partes:
        if actual and len(sep.join(actual + [parte])) > tam:
            chunks.append(sep.join(actual))
            # Conservamos solo la cola del chunk anterior (el solapamiento)
            while actual and (len(sep.join(actual)) > solape or len(sep.join(actual + [parte])) > tam):
                actual.pop(0)
        actual.append(parte)
    if actual:
        chunks.append(sep.join(actual))
    return chunks


def dividir(texto: str, tam: int = 800, solape: int = 150, separadores: list[str] = SEPARADORES) -> list[str]:
    if solape >= tam:
        raise ValueError("El solapamiento debe ser menor que el tamaño del chunk")

    sep = next((s for s in separadores if s and s in texto), "")
    resto = separadores[separadores.index(sep) + 1:] if sep in separadores else []
    partes = texto.split(sep) if sep else list(texto)

    chunks: list[str] = []
    pequenas: list[str] = []
    for parte in partes:
        if len(parte) <= tam:
            pequenas.append(parte)
            continue
        # Esta parte es demasiado grande: cerramos lo acumulado y la partimos con separadores más finos
        if pequenas:
            chunks.extend(unir(pequenas, sep, tam, solape))
            pequenas = []
        chunks.extend(dividir(parte, tam, solape, resto))
    if pequenas:
        chunks.extend(unir(pequenas, sep, tam, solape))
    return [c.strip() for c in chunks if c.strip()]

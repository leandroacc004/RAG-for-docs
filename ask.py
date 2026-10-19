"""Paso 2 del RAG: buscar los chunks relevantes y pedirle a Claude que responda con ellos."""

import argparse
import json
import sys
from pathlib import Path

import anthropic

from bm25 import BM25
from llm import ErrorLLM, crear_mensaje, texto

SYSTEM = (
    "Respondes preguntas usando únicamente los fragmentos de documentos que se te entregan. "
    "Cita cada afirmación con el id del fragmento entre corchetes, por ejemplo [politica_vacaciones.md#2]. "
    "Si los fragmentos no contienen la respuesta, dilo claramente en vez de suponer. Responde en español."
)


def armar_contexto(chunks: list[dict]) -> str:
    """Cada chunk va con su id y el título de su documento: así Claude puede citarlo y sabe de dónde viene."""
    bloques = [
        f'<fragmento id="{c["id"]}" documento="{c["titulo"]}">\n{c["texto"]}\n</fragmento>' for c in chunks
    ]
    return "<fragmentos>\n" + "\n".join(bloques) + "\n</fragmentos>"


def responder(pregunta: str, chunks: list[dict], buscador: BM25, k: int, ver_chunks: bool) -> None:
    resultados = buscador.buscar(pregunta, k)
    if not resultados:
        print("Ningún fragmento coincide con la pregunta. Prueba con otras palabras.\n")
        return

    seleccion = [chunks[i] for i, _ in resultados]
    print("Fragmentos recuperados: " + ", ".join(f"{chunks[i]['id']} ({p:.2f})" for i, p in resultados))
    if ver_chunks:
        for c in seleccion:
            print(f"\n--- {c['id']} ---\n{c['texto']}")

    # Los documentos van primero y la pregunta al final: Claude rinde mejor con contexto largo en ese orden.
    prompt = f"{armar_contexto(seleccion)}\n\nPregunta: {pregunta}"
    try:
        resp = crear_mensaje(max_tokens=16000, system=SYSTEM, messages=[{"role": "user", "content": prompt}])
        print(f"\n{texto(resp)}\n")
    except ErrorLLM as e:
        print(f"\nNo se pudo responder: {e}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Pregunta a tus documentos.")
    parser.add_argument("pregunta", nargs="?", help="Si no la pasas, entra en modo interactivo")
    parser.add_argument("--indice", type=Path, default=Path("indice.json"))
    parser.add_argument("--k", type=int, default=4, help="Cuántos chunks enviar a Claude")
    parser.add_argument("--ver-chunks", action="store_true", help="Mostrar el texto de los chunks recuperados")
    args = parser.parse_args()

    if not args.indice.exists():
        print(f"No existe {args.indice}. Ejecuta primero: python ingest.py")
        return 1
    chunks = json.loads(args.indice.read_text(encoding="utf-8"))["chunks"]
    # Indexamos título + texto: el título aporta contexto que el chunk suelto a veces no tiene
    buscador = BM25([f"{c['titulo']}\n{c['texto']}" for c in chunks])

    try:
        if args.pregunta:
            responder(args.pregunta, chunks, buscador, args.k, args.ver_chunks)
            return 0
        print("Modo interactivo. Escribe tu pregunta (o 'salir').")
        while True:
            pregunta = input("> ").strip()
            if pregunta.lower() in {"salir", "exit", "quit"}:
                return 0
            if pregunta:
                responder(pregunta, chunks, buscador, args.k, args.ver_chunks)
    except anthropic.APIError as e:
        print(f"Error de la API de Claude: {e}")
        return 1
    except (KeyboardInterrupt, EOFError):
        return 0


if __name__ == "__main__":
    sys.exit(main())

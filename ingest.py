"""Paso 1 del RAG: leer documentos, partirlos en chunks y guardar el índice."""

import argparse
import json
import sys
from pathlib import Path

from chunker import dividir

EXTENSIONES = {".md", ".txt"}


def titulo_de(texto: str, archivo: Path) -> str:
    for linea in texto.splitlines():
        if linea.startswith("# "):
            return linea[2:].strip()
    return archivo.stem


def main() -> int:
    parser = argparse.ArgumentParser(description="Crea el índice de chunks a partir de tus documentos.")
    parser.add_argument("--docs", type=Path, default=Path("docs"), help="Carpeta con documentos .md/.txt")
    parser.add_argument("--salida", type=Path, default=Path("indice.json"))
    parser.add_argument("--tam", type=int, default=800, help="Tamaño máximo de cada chunk en caracteres")
    parser.add_argument("--solape", type=int, default=150, help="Caracteres repetidos entre chunks consecutivos")
    parser.add_argument("--ver", action="store_true", help="Mostrar cada chunk generado")
    args = parser.parse_args()

    archivos = sorted(p for p in args.docs.rglob("*") if p.suffix.lower() in EXTENSIONES)
    if not archivos:
        print(f"No encontré documentos .md o .txt en {args.docs}")
        return 1

    chunks = []
    for archivo in archivos:
        texto = archivo.read_text(encoding="utf-8")
        titulo = titulo_de(texto, archivo)
        fuente = archivo.relative_to(args.docs).as_posix()
        partes = dividir(texto, args.tam, args.solape)
        for n, parte in enumerate(partes):
            chunks.append({"id": f"{fuente}#{n}", "fuente": fuente, "titulo": titulo, "texto": parte})
        print(f"{fuente}: {len(texto)} caracteres -> {len(partes)} chunks")

    if args.ver:
        for c in chunks:
            print(f"\n--- {c['id']} ({len(c['texto'])} caracteres) ---\n{c['texto']}")

    indice = {"config": {"tam": args.tam, "solape": args.solape}, "chunks": chunks}
    args.salida.write_text(json.dumps(indice, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nÍndice guardado en {args.salida} ({len(chunks)} chunks)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

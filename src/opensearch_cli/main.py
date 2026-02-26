"""
CLI pour inspecter OpenSearch sans passer par le dashboard.

Usage:
    os-cli --list
    os-cli <collection> --limit 20
    os-cli <collection> --limit 20 --show-embedding
"""

import argparse
import json
import os
from urllib.parse import urlparse

from dotenv import load_dotenv
from opensearchpy import OpenSearch
from rich.console import Console
from rich.table import Table

from opensearch_cli.helpers import black_list

load_dotenv()

console = Console()


def _get_client() -> OpenSearch:
    """Build OpenSearch client from env vars."""
    raw = os.getenv("OPENSEARCH_URL", "")
    host = "localhost"
    port = 9200
    auth = None
    use_ssl = False

    if raw:
        try:
            config = json.loads(raw)
            parsed = urlparse(config["endpoint"])
            host = parsed.hostname or "localhost"
            port = parsed.port or 443
            auth = (config.get("username", "admin"), config.get("password", ""))
            use_ssl = True
        except (json.JSONDecodeError, KeyError):
            parsed = urlparse(raw)
            host = parsed.hostname or "localhost"
            port = parsed.port or 9200
            use_ssl = parsed.scheme == "https"
    else:
        host = os.getenv("OPENSEARCH_HOST", "localhost")
        port = int(os.getenv("OPENSEARCH_PORT", "9200"))

    return OpenSearch(
        hosts=[{"host": host, "port": port}],
        http_compress=True,
        use_ssl=use_ssl,
        verify_certs=use_ssl,
        ssl_assert_hostname=False,
        ssl_show_warn=False,
        http_auth=auth,
    )


def list_indices(client: OpenSearch) -> None:
    """List all indices with doc count and size."""
    indices = client.cat.indices(format="json")
    if not indices:
        console.print("[yellow]Aucun index trouvé.[/yellow]")
        return

    indices.sort(key=lambda x: x.get("index", ""))

    table = Table(title="Index OpenSearch")
    table.add_column("Index", style="cyan", no_wrap=True)
    table.add_column("Docs", justify="right", style="green")
    table.add_column("Taille", justify="right", style="magenta")
    table.add_column("Health", style="bold")
    table.add_column("Status")

    health_colors = {"green": "green", "yellow": "yellow", "red": "red"}

    for idx in indices:
        name = idx.get("index", "?")
        docs = idx.get("docs.count", "0")
        size = idx.get("store.size", "?")
        health = idx.get("health", "?")
        status = idx.get("status", "?")
        color = health_colors.get(health, "white")
        health_display = f"[{color}]{health}[/{color}]"
        table.add_row(name, docs, size, health_display, status)

    console.print(table)
    console.print(f"\n[dim]{len(indices)} index au total[/dim]")


def show_collection(
    client: OpenSearch,
    collection: str,
    limit: int,
    show_embedding: bool,
) -> None:
    """Show documents from a collection."""
    if not client.indices.exists(index=collection):
        console.print(f"[red]L'index '{collection}' n'existe pas.[/red]")
        console.print("[dim]Utilisez --list pour voir les index disponibles.[/dim]")
        return

    response = client.search(
        index=collection,
        body={"size": limit, "query": {"match_all": {}}},
    )

    hits = response.get("hits", {})
    total = hits.get("total", {}).get("value", 0)
    documents = hits.get("hits", [])

    console.print(
        f"\n[bold]{collection}[/bold]  —  "
        f"[green]{len(documents)}[/green]/{total} documents"
        f"{'' if show_embedding else '  [dim](embeddings masqués)[/dim]'}\n"
    )

    if not documents:
        console.print("[yellow]Aucun document dans cet index.[/yellow]")
        return

    for doc in documents:
        source = doc.get("_source", {})
        if not show_embedding:
            source = black_list(source, ["embedding"])
        console.print(f"[cyan bold]_id:[/cyan bold] {doc.get('_id', '?')}")
        console.print_json(json.dumps(source, ensure_ascii=False, default=str))
        console.print("[dim]─[/dim]" * 40)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CLI pour inspecter OpenSearch",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Exemples:\n"
            "  os-cli --list\n"
            "  os-cli org_xxx_source_yyy --limit 20\n"
            "  os-cli org_xxx_source_yyy --show-embedding\n"
        ),
    )
    parser.add_argument("collection", nargs="?", help="Nom de l'index à inspecter")
    parser.add_argument("--list", action="store_true", help="Lister tous les index")
    parser.add_argument(
        "--limit", type=int, default=10, help="Nombre de documents (défaut: 10)"
    )
    parser.add_argument(
        "--show-embedding",
        action="store_true",
        help="Afficher les vecteurs d'embedding",
    )
    args = parser.parse_args()

    if not args.list and not args.collection:
        parser.print_help()
        return

    client = _get_client()

    if args.list:
        list_indices(client)
    else:
        show_collection(client, args.collection, args.limit, args.show_embedding)


if __name__ == "__main__":
    main()

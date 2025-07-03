#!/usr/bin/env python3

import os
import json
import argparse
import requests
from rich.console import Console
from rich.syntax import Syntax
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()  # Charge les variables depuis .env

console = Console()
DOMAIN_FIELDS = {"domainName", "domainHandle", "nameServer"}

API_URL_PROD = "https://secure.brandshelter.com/graphql"
API_URL_DEV = "https://app.dev.bs-srv.net/graphql"


def get_token():
    token = os.getenv("BRANDSHELTER_TOKEN")
    if not token:
        console.print("[bold red]❌ Token JWT manquant. Définis BRANDSHELTER_TOKEN dans .env ou ton environnement.[/]")
        exit(1)
    return token


def make_headers():
    return {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {get_token()}",
    }


def query_graphql(endpoint, query, verbose=False, variables=None):
    def render_query_with_values(query, variables):
        if not variables:
            return query
        rendered = query
        for k, v in variables.items():
            if isinstance(v, str):
                v_str = f'"{v}"'
            else:
                v_str = str(v)
            # Remplace $var dans la requête par la valeur (pour affichage uniquement)
            rendered = rendered.replace(f'${k}', v_str)
        return rendered

    if verbose:
        console.print("[bold green]📤 Requête GraphQL envoyée :[/]")
        console.print(Syntax(query, "graphql", theme="monokai"))
        if variables:
            console.print("[bold yellow]📦 Variables :[/]")
            console.print(Syntax(json.dumps(variables, indent=2, ensure_ascii=False), "json", theme="monokai"))
            console.print("[bold cyan]🔎 Requête avec valeurs :[/]")
            console.print(Syntax(render_query_with_values(query, variables), "graphql", theme="monokai"))

    try:
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        resp = requests.post(endpoint, headers=make_headers(), json=payload)
        resp.raise_for_status()
        data = resp.json()
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        console.print(Syntax(json_str, "json", theme="monokai", line_numbers=False))
        return data
    except Exception as e:
        console.print(f"[bold red]❌ Erreur API :[/] {e}")
        console.print(resp.text if resp else "")
        return None


def paginate_monitorings(dev=False, verbose=False, limit=None, createdAtGt=None):
    url = API_URL_DEV if dev else API_URL_PROD
    if not createdAtGt:
        createdAtGt = datetime.now().strftime("%Y-%m-%dT00:00:00Z")
    query = """
    query ($first: Int, $after: String, $createdAtGt: ISO8601DateTime) {
      monitoringsSafebrands(first: $first, after: $after, createdAtGt: $createdAtGt) {
        nodes {
          id
          __typename
          referenceNumber
          createdAt
        }

        pageInfo {
          hasNextPage
          endCursor
        }
      }
    }
    """

    first = 100
    after = None
    total = 0

    while True:
        if limit is not None:
            remaining = limit - total
            if remaining <= 0:
                break
            batch_size = min(first, remaining)
        else:
            batch_size = first
        variables = {"first": batch_size, "after": after, "createdAtGt": createdAtGt}
        data = query_graphql(url, query, verbose=verbose, variables=variables)
        if not data:
            break

        monitorings = data.get("data", {}).get("monitoringsSafebrands", {})
        nodes = monitorings.get("nodes", [])
        page_info = monitorings.get("pageInfo", {})

        for node in nodes:
            console.print(Syntax(json.dumps(node, indent=2, ensure_ascii=False), "json"))

        total += len(nodes)
        if verbose:
            console.print(f"[blue]🔁 Page suivante : {page_info.get('endCursor')}[/]")

        if not page_info.get("hasNextPage") or (limit is not None and total >= limit):
            break
        after = page_info.get("endCursor")

    console.print(f"[bold green]✅ {total} monitorings récupérés.[/]")


def query_custom(field, value, dev=False, verbose=False):
    url = API_URL_DEV if dev else API_URL_PROD

    if field == "clientNumber" and len(value) < 8:
        value = value.zfill(10) + "-1"

    if field in DOMAIN_FIELDS:
        query = f"""
        query {{
            domains({field}: "{value}") {{
                nodes {{
                    account {{
                        id
                        clientNumber
                        company
                    }}
                }}
            }}
        }}
        """
    else:
        query = f"""
        query {{
            userSafebrands(findUserInput: {{
                {field}: "{value}"
            }}) {{
                id
                clientNumber
                login
                authorization {{
                    permissions {{
                        action
                        department {{ id name }}
                        id
                        requireApproval
                        requireTan
                        subjectClass
                    }}
                }}
                account {{
                    id
                    clientNumber
                    company
                    parent {{ id clientNumber }}
                }}
            }}
        }}
        """
    query_graphql(url, query, verbose)


def main():
    parser = argparse.ArgumentParser(description="CLI GraphQL Brandshelter", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("field", nargs="?", help="Champ à interroger (ex: loginName, clientNumber, domainName)")
    parser.add_argument("value", nargs="?", help="Valeur du champ")
    parser.add_argument("--dev", action="store_true", help="Utiliser l'environnement de développement")
    parser.add_argument("--verbose", action="store_true", help="Afficher la requête envoyée")
    parser.add_argument("--monitorings", action="store_true", help="Lister tous les monitorings (avec pagination)")
    parser.add_argument("--limit", type=int, help="Nombre maximum de monitorings à récupérer (avec --monitorings)")
    parser.add_argument("--createdAtGt", type=str, help="Date ISO8601 (ex: 2025-07-02T00:00:00Z) pour filtrer les monitorings créés après cette date (avec --monitorings)")

    args = parser.parse_args()

    if args.monitorings:
        paginate_monitorings(dev=args.dev, verbose=args.verbose, limit=args.limit, createdAtGt=args.createdAtGt)
    elif args.field and args.value:
        query_custom(args.field, args.value, dev=args.dev, verbose=args.verbose)
    else:
        console.print("[bold red]❌ Il faut spécifier --monitorings ou un champ + une valeur (ex: login fabrice.terrasson)[/]")
        parser.print_help()


if __name__ == "__main__":
    main()

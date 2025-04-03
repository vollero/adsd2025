#!/usr/bin/env python3
"""
Client di test per il Key-Value Store Distribuito
"""

import sys
import json
import argparse
import requests
import time

def print_colored(text, color):
    """Stampa testo colorato"""
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "blue": "\033[94m",
        "yellow": "\033[93m",
        "reset": "\033[0m"
    }
    print(f"{colors.get(color, '')}{text}{colors['reset']}")

def main():
    parser = argparse.ArgumentParser(description="Client di test per il Key-Value Store Distribuito")
    parser.add_argument("--host", default="localhost", help="Hostname del coordinatore")
    parser.add_argument("--port", default=8000, type=int, help="Porta del coordinatore")
    
    subparsers = parser.add_subparsers(dest="command", help="Comandi disponibili")
    
    # Comando GET
    get_parser = subparsers.add_parser("get", help="Ottiene il valore di una chiave")
    get_parser.add_argument("key", help="Chiave da cercare")
    
    # Comando PUT
    put_parser = subparsers.add_parser("put", help="Inserisce o aggiorna il valore di una chiave")
    put_parser.add_argument("key", help="Chiave da inserire/aggiornare")
    put_parser.add_argument("value", help="Valore da associare alla chiave")
    
    # Comando DELETE
    delete_parser = subparsers.add_parser("delete", help="Elimina una chiave")
    delete_parser.add_argument("key", help="Chiave da eliminare")
    
    # Comando KEYS
    subparsers.add_parser("keys", help="Ottiene tutte le chiavi presenti")
    
    # Comando STATS
    subparsers.add_parser("stats", help="Ottiene le statistiche")
    
    # Comando TEST
    test_parser = subparsers.add_parser("test", help="Esegue un test di carico")
    test_parser.add_argument("--count", type=int, default=100, help="Numero di operazioni da eseguire")
    
    args = parser.parse_args()
    
    base_url = f"http://{args.host}:{args.port}"
    
    if args.command == "get":
        try:
            response = requests.get(f"{base_url}/key/{args.key}")
            if response.status_code == 200:
                data = response.json()
                print_colored(f"Chiave: {args.key}", "blue")
                print_colored(f"Valore: {data['value']}", "green")
                print_colored(f"Quorum: {data['quorum_size']}", "blue")
                print("\nRisposte dai nodi:")
                for resp in data['responses']:
                    status = "✓" if resp['success'] else "✗"
                    color = "green" if resp['success'] else "red"
                    print_colored(f"  {status} {resp['node']}: {'OK' if resp['success'] else resp['error']}", color)
            else:
                print_colored(f"Errore: {response.status_code} - {response.text}", "red")
        except Exception as e:
            print_colored(f"Errore: {str(e)}", "red")
    
    elif args.command == "put":
        try:
            response = requests.put(f"{base_url}/key/{args.key}", json={"value": args.value})
            if response.status_code == 200:
                data = response.json()
                print_colored(f"Chiave '{args.key}' aggiornata con valore '{args.value}'", "green")
                print_colored(f"Nodi aggiornati: {sum(1 for r in data['responses'] if r['success'])}/{len(data['responses'])}", "blue")
                print("\nRisposte dai nodi:")
                for resp in data['responses']:
                    status = "✓" if resp['success'] else "✗"
                    color = "green" if resp['success'] else "red"
                    print_colored(f"  {status} {resp['node']}: {'OK' if resp['success'] else resp['error']}", color)
            else:
                print_colored(f"Errore: {response.status_code} - {response.text}", "red")
        except Exception as e:
            print_colored(f"Errore: {str(e)}", "red")
    
    elif args.command == "delete":
        try:
            response = requests.delete(f"{base_url}/key/{args.key}")
            if response.status_code == 200:
                data = response.json()
                print_colored(f"Chiave '{args.key}' eliminata", "green")
                print_colored(f"Messaggio: {data['message']}", "blue")
            else:
                print_colored(f"Errore: {response.status_code} - {response.text}", "red")
        except Exception as e:
            print_colored(f"Errore: {str(e)}", "red")
    
    elif args.command == "keys":
        try:
            response = requests.get(f"{base_url}/keys")
            if response.status_code == 200:
                data = response.json()
                if data['keys']:
                    print_colored("Chiavi presenti:", "blue")
                    for key in data['keys']:
                        print(f"  - {key}")
                else:
                    print_colored("Nessuna chiave presente nel sistema", "yellow")
            else:
                print_colored(f"Errore: {response.status_code} - {response.text}", "red")
        except Exception as e:
            print_colored(f"Errore: {str(e)}", "red")
    
    elif args.command == "stats":
        try:
            response = requests.get(f"{base_url}/stats")
            if response.status_code == 200:
                data = response.json()
                print_colored("Statistiche del coordinatore:", "blue")
                print(f"  - Nodi configurati: {data['coordinator']['nodes_configured']}")
                print(f"  - Nodi rispondenti: {data['coordinator']['nodes_responding']}")
                print(f"  - Dimensione quorum: {data['coordinator']['quorum_size']}")
                
                print_colored("\nStatistiche dei nodi:", "blue")
                for node, stats in data['nodes'].items():
                    print_colored(f"  Nodo: {node}", "green")
                    if 'cache' in stats:
                        cache = stats['cache']
                        print(f"    - Elementi in cache: {cache['items_count']}/{cache['max_items']}")
                        print(f"    - Dimensione cache: {cache['size_bytes']}/{cache['max_size_bytes']} bytes")
                        print(f"    - Utilizzo: {cache['utilization_percent']}%")
                    print(f"    - Elementi nel DB: {stats.get('db_size', 'N/A')}")
                    print(f"    - Elementi nella cronologia: {stats.get('history_count', 'N/A')}")
                    print(f"    - Operazioni in attesa: {stats.get('pending_operations', 'N/A')}")
            else:
                print_colored(f"Errore: {response.status_code} - {response.text}", "red")
        except Exception as e:
            print_colored(f"Errore: {str(e)}", "red")
    
    elif args.command == "test":
        print_colored(f"Esecuzione test di carico con {args.count} operazioni...", "blue")
        start_time = time.time()
        
        # Test di scrittura
        print_colored("Test di scrittura...", "yellow")
        write_success = 0
        for i in range(args.count):
            try:
                response = requests.put(f"{base_url}/key/test_key_{i}", json={"value": f"test_value_{i}"})
                if response.status_code == 200:
                    write_success += 1
                if i % 10 == 0:
                    sys.stdout.write(f"\rCompletato: {i}/{args.count}")
                    sys.stdout.flush()
            except Exception:
                pass
        print(f"\rCompletato: {args.count}/{args.count}")
        print_colored(f"Scritture riuscite: {write_success}/{args.count} ({write_success/args.count*100:.1f}%)", "green")
        
        # Test di lettura
        print_colored("\nTest di lettura...", "yellow")
        read_success = 0
        for i in range(args.count):
            try:
                response = requests.get(f"{base_url}/key/test_key_{i}")
                if response.status_code == 200:
                    read_success += 1
                if i % 10 == 0:
                    sys.stdout.write(f"\rCompletato: {i}/{args.count}")
                    sys.stdout.flush()
            except Exception:
                pass
        print(f"\rCompletato: {args.count}/{args.count}")
        print_colored(f"Letture riuscite: {read_success}/{args.count} ({read_success/args.count*100:.1f}%)", "green")
        
        elapsed_time = time.time() - start_time
        ops_per_second = args.count * 2 / elapsed_time
        print_colored(f"\nTest completato in {elapsed_time:.2f} secondi", "blue")
        print_colored(f"Operazioni al secondo: {ops_per_second:.2f}", "blue")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

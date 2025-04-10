#!/usr/bin/env python3
"""
Client di test per il Key-Value Store Distribuito con Sharding
"""

import sys
import json
import argparse
import requests
import time
import random
import string

def print_colored(text, color):
    """Stampa testo colorato"""
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "blue": "\033[94m",
        "yellow": "\033[93m",
        "cyan": "\033[96m",
        "reset": "\033[0m"
    }
    print(f"{colors.get(color, '')}{text}{colors['reset']}")

def generate_random_key(length=8):
    """Genera una chiave casuale"""
    return ''.join(random.choice(string.ascii_lowercase) for _ in range(length))

def generate_random_value(length=16):
    """Genera un valore casuale"""
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

def main():
    parser = argparse.ArgumentParser(description="Client di test per il Key-Value Store Distribuito con Sharding")
    parser.add_argument("--host", default="localhost", help="Hostname del coordinatore")
    parser.add_argument("--port", default=8020, type=int, help="Porta del coordinatore")
    
    subparsers = parser.add_subparsers(dest="command", help="Comandi disponibili")
    
    # Comandi per il key-value store
    get_parser = subparsers.add_parser("get", help="Ottiene il valore di una chiave")
    get_parser.add_argument("key", help="Chiave da cercare")
    
    put_parser = subparsers.add_parser("put", help="Inserisce o aggiorna il valore di una chiave")
    put_parser.add_argument("key", help="Chiave da inserire/aggiornare")
    put_parser.add_argument("value", help="Valore da associare alla chiave")
    
    delete_parser = subparsers.add_parser("delete", help="Elimina una chiave")
    delete_parser.add_argument("key", help="Chiave da eliminare")
    
    subparsers.add_parser("keys", help="Ottiene tutte le chiavi presenti")
    
    # Comandi per lo sharding
    subparsers.add_parser("sharding-info", help="Ottiene informazioni sulla configurazione dello sharding")
    
    node_for_key_parser = subparsers.add_parser("node-for-key", help="Ottiene i nodi responsabili per una chiave")
    node_for_key_parser.add_argument("key", help="Chiave da cercare")
    
    node_keys_parser = subparsers.add_parser("node-keys", help="Ottiene le chiavi su un nodo specifico")
    node_keys_parser.add_argument("node", help="Nodo da interrogare (es. 'kvstore1:8050')")
    
    ring_parser = subparsers.add_parser("ring", help="Visualizza la struttura dell'hash ring")
    
    reconfigure_parser = subparsers.add_parser("reconfigure", help="Riconfigura lo sharding")
    reconfigure_parser.add_argument("--replication-factor", "-r", type=float, required=True, 
                              help="Nuovo fattore di replica (0.0-1.0)")
    reconfigure_parser.add_argument("--virtual-nodes", "-v", type=int, required=True, 
                              help="Nuovo numero di nodi virtuali per nodo fisico")
    
    rebalance_parser = subparsers.add_parser("rebalance", help="Ribilancia le chiavi tra i nodi")
    
    # Comandi di test
    test_parser = subparsers.add_parser("test", help="Esegue un test di carico")
    test_parser.add_argument("--count", type=int, default=100, help="Numero di operazioni da eseguire")
    
    distribution_test_parser = subparsers.add_parser("test-distribution", 
                                               help="Testa la distribuzione delle chiavi tra i nodi")
    distribution_test_parser.add_argument("--count", type=int, default=1000, 
                                    help="Numero di chiavi da generare per il test")
    
    subparsers.add_parser("stats", help="Ottiene le statistiche")
    
    args = parser.parse_args()
    
    base_url = f"http://{args.host}:{args.port}"
    
    # Comandi del key-value store
    if args.command == "get":
        try:
            response = requests.get(f"{base_url}/key/{args.key}")
            if response.status_code == 200:
                data = response.json()
                print_colored(f"Chiave: {args.key}", "blue")
                print_colored(f"Valore: {data['value']}", "green")
                print_colored(f"Repliche: {data['replicas']}", "blue")
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
                print_colored(f"Repliche: {data['replicas']}", "blue")
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
    
    # Comandi dello sharding
    elif args.command == "sharding-info":
        try:
            response = requests.get(f"{base_url}/sharding/info")
            if response.status_code == 200:
                data = response.json()
                print_colored("Informazioni sullo sharding:", "blue")
                print(f"  - Nodi totali: {data['total_nodes']}")
                print(f"  - Fattore di replica: {data['replication_factor']}")
                print(f"  - Nodi virtuali per nodo: {data['virtual_nodes_per_node']}")
                print(f"  - Nodi virtuali totali: {data['total_virtual_nodes']}")
                
                print_colored("\nDistribuzione delle chiavi:", "blue")
                for node, count in data['key_distribution'].items():
                    print(f"  - {node}: {count} chiavi")
            else:
                print_colored(f"Errore: {response.status_code} - {response.text}", "red")
        except Exception as e:
            print_colored(f"Errore: {str(e)}", "red")
    
    elif args.command == "node-for-key":
        try:
            response = requests.get(f"{base_url}/sharding/node-for-key/{args.key}")
            if response.status_code == 200:
                data = response.json()
                print_colored(f"Nodi responsabili per la chiave '{args.key}':", "blue")
                print(f"  - Numero di repliche: {data['replica_count']}")
                print_colored("  - Nodi:", "green")
                for node in data['responsible_nodes']:
                    print(f"    * {node}")
            else:
                print_colored(f"Errore: {response.status_code} - {response.text}", "red")
        except Exception as e:
            print_colored(f"Errore: {str(e)}", "red")
    
    elif args.command == "node-keys":
        try:
            response = requests.get(f"{base_url}/sharding/node-keys/{args.node}")
            if response.status_code == 200:
                data = response.json()
                print_colored(f"Chiavi presenti sul nodo '{args.node}':", "blue")
                print(f"  - Numero di chiavi: {data['keys_count']}")
                if data['keys']:
                    print_colored("  - Chiavi:", "green")
                    for key in data['keys']:
                        print(f"    * {key}")
                else:
                    print_colored("  - Nessuna chiave presente sul nodo", "yellow")
            else:
                print_colored(f"Errore: {response.status_code} - {response.text}", "red")
        except Exception as e:
            print_colored(f"Errore: {str(e)}", "red")
    
    elif args.command == "ring":
        try:
            response = requests.get(f"{base_url}/sharding/ring")
            if response.status_code == 200:
                data = response.json()
                print_colored("Informazioni sull'hash ring:", "blue")
                print(f"  - Nodi fisici: {data['total_nodes']}")
                print(f"  - Nodi virtuali: {data['virtual_nodes']}")
                
                print_colored("\nDistribuzione dei nodi virtuali:", "green")
                for node, count in data['distribution'].items():
                    print(f"  - {node}: {count} nodi virtuali")
                
                print_colored("\nPrimi 10 nodi dell'anello (per posizione):", "cyan")
                for i, node_info in enumerate(data['ring'][:10]):
                    print(f"  {i+1}. Posizione: {node_info['position']}, Nodo: {node_info['node']}")
            else:
                print_colored(f"Errore: {response.status_code} - {response.text}", "red")
        except Exception as e:
            print_colored(f"Errore: {str(e)}", "red")
    
    elif args.command == "reconfigure":
        try:
            response = requests.post(f"{base_url}/sharding/reconfigure", 
                                   json={"replication_factor": args.replication_factor, 
                                         "virtual_nodes": args.virtual_nodes})
            if response.status_code == 200:
                data = response.json()
                print_colored("Sharding riconfigurato con successo:", "green")
                print_colored("Configurazione precedente:", "blue")
                print(f"  - Fattore di replica: {data['old_config']['replication_factor']}")
                print(f"  - Nodi virtuali: {data['old_config']['virtual_nodes']}")
                print_colored("Nuova configurazione:", "blue")
                print(f"  - Fattore di replica: {data['new_config']['replication_factor']}")
                print(f"  - Nodi virtuali: {data['new_config']['virtual_nodes']}")
                print_colored("\nNota: È consigliabile eseguire un ribilanciamento per applicare la nuova configurazione", "yellow")
                print_colored("      ./test_client.py rebalance", "yellow")
            else:
                print_colored(f"Errore: {response.status_code} - {response.text}", "red")
        except Exception as e:
            print_colored(f"Errore: {str(e)}", "red")
    
    elif args.command == "rebalance":
        try:
            print_colored("Avvio del ribilanciamento delle chiavi...", "blue")
            print_colored("Questa operazione potrebbe richiedere tempo a seconda del numero di chiavi.", "yellow")
            
            response = requests.post(f"{base_url}/rebalance")
            if response.status_code == 200:
                data = response.json()
                print_colored("Ribilanciamento completato:", "green")
                print(f"  - Chiavi totali: {data['details']['total_keys']}")
                print(f"  - Chiavi ribilanciate: {data['details']['rebalanced_keys']}")
                print(f"  - Operazioni totali: {data['details']['total_operations']}")
                print(f"  - Operazioni fallite: {data['details']['failed_operations']}")
            else:
                print_colored(f"Errore: {response.status_code} - {response.text}", "red")
        except Exception as e:
            print_colored(f"Errore: {str(e)}", "red")
    
    # Comandi di test
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
    
    elif args.command == "test-distribution":
        print_colored(f"Test di distribuzione con {args.count} chiavi...", "blue")
        
        # Genera chiavi casuali
        keys = [generate_random_key() for _ in range(args.count)]
        
        # Per ogni chiave, ottieni i nodi responsabili
        node_counters = {}
        
        print_colored("Analisi della distribuzione delle chiavi...", "yellow")
        for i, key in enumerate(keys):
            try:
                response = requests.get(f"{base_url}/sharding/node-for-key/{key}")
                if response.status_code == 200:
                    data = response.json()
                    for node in data['responsible_nodes']:
                        if node in node_counters:
                            node_counters[node] += 1
                        else:
                            node_counters[node] = 1
                
                if i % 100 == 0:
                    sys.stdout.write(f"\rAnalizzate: {i}/{args.count} chiavi")
                    sys.stdout.flush()
            except Exception:
                pass
        
        print(f"\rAnalizzate: {args.count}/{args.count} chiavi")
        
        # Visualizza la distribuzione
        print_colored("\nDistribuzione delle chiavi tra i nodi:", "green")
        total_key_assignments = sum(node_counters.values())
        
        for node, count in sorted(node_counters.items(), key=lambda x: x[0]):
            percentage = count / total_key_assignments * 100
            bar_length = int(percentage / 2)
            bar = "█" * bar_length
            print(f"  {node}: {count} chiavi ({percentage:.2f}%) {bar}")
        
        # Statistiche sulla distribuzione
        min_count = min(node_counters.values())
        max_count = max(node_counters.values())
        avg_count = total_key_assignments / len(node_counters)
        
        # Calcola la deviazione standard
        variance = sum((count - avg_count) ** 2 for count in node_counters.values()) / len(node_counters)
        std_dev = variance ** 0.5
        
        print_colored("\nStatistiche sulla distribuzione:", "blue")
        print(f"  - Numero di nodi: {len(node_counters)}")
        print(f"  - Assegnamenti totali: {total_key_assignments}")
        print(f"  - Minimo per nodo: {min_count}")
        print(f"  - Massimo per nodo: {max_count}")
        print(f"  - Media per nodo: {avg_count:.2f}")
        print(f"  - Deviazione standard: {std_dev:.2f}")
        print(f"  - Coefficiente di variazione: {(std_dev / avg_count * 100):.2f}%")
    
    elif args.command == "stats":
        try:
            response = requests.get(f"{base_url}/stats")
            if response.status_code == 200:
                data = response.json()
                print_colored("Statistiche del coordinatore:", "blue")
                print(f"  - Nodi configurati: {data['coordinator']['nodes_configured']}")
                print(f"  - Nodi rispondenti: {data['coordinator']['nodes_responding']}")
                print(f"  - Fattore di replica: {data['coordinator']['replication_factor']}")
                print(f"  - Nodi virtuali: {data['coordinator']['virtual_nodes']}")
                
                if 'sharding' in data:
                    print_colored("\nStatistiche di sharding:", "blue")
                    print("  - Distribuzione dei nodi virtuali:")
                    for node, count in data['sharding']['virtual_node_distribution'].items():
                        print(f"    * {node}: {count} nodi virtuali")
                
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
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

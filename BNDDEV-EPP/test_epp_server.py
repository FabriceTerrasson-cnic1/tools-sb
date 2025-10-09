#!/usr/bin/env python3
"""
Serveur EPP de test pour valider le tunnel Python
Simule le comportement du serveur epp.gtld.knet.cn:700
"""
import socket
import ssl
import struct
import threading

def create_epp_greeting():
    """Crée un greeting EPP de test"""
    greeting = '''<?xml version="1.0" encoding="UTF-8"?>
<epp xmlns="urn:ietf:params:xml:ns:epp-1.0">
<greeting>
<svID>TEST EPP Server</svID>
<svDate>2025-10-09T09:30:00.000Z</svDate>
<svcMenu>
<version>1.0</version>
<lang>en</lang>
<objURI>urn:ietf:params:xml:ns:domain-1.0</objURI>
<objURI>urn:ietf:params:xml:ns:contact-1.0</objURI>
<objURI>urn:ietf:params:xml:ns:host-1.0</objURI>
</svcMenu>
<dcp>
<access><all/></access>
<statement>
<purpose><admin/><prov/></purpose>
<recipient><ours/><public/></recipient>
<retention><stated/></retention>
</statement>
</dcp>
</greeting>
</epp>'''
    
    # Format binaire EPP
    xml_bytes = greeting.encode('utf-8')
    length = len(xml_bytes) + 4
    return struct.pack('>I', length) + xml_bytes

def handle_client(client_socket):
    """Gère une connexion client de test"""
    try:
        print(f"📞 Client connecté: {client_socket.getpeername()}")
        
        # Envoie le greeting EPP
        greeting = create_epp_greeting()
        client_socket.send(greeting)
        print(f"📤 Greeting EPP envoyé ({len(greeting)} octets)")
        
        # Écoute les commandes
        while True:
            try:
                # Lit longueur
                length_data = client_socket.recv(4)
                if not length_data:
                    break
                    
                length = struct.unpack('>I', length_data)[0] - 4
                
                # Lit commande
                command_data = client_socket.recv(length)
                command = command_data.decode('utf-8')
                
                print(f"📥 Commande reçue: {command[:100]}...")
                
                # Réponse générique
                response = '''<?xml version="1.0" encoding="UTF-8"?>
<epp xmlns="urn:ietf:params:xml:ns:epp-1.0">
<response>
<result code="1000">
<msg>Command completed successfully</msg>
</result>
<trID>
<clTRID>TEST</clTRID>
<svTRID>TEST-RESPONSE</svTRID>
</trID>
</response>
</epp>'''
                
                # Format binaire
                resp_bytes = response.encode('utf-8')
                resp_length = len(resp_bytes) + 4
                resp_message = struct.pack('>I', resp_length) + resp_bytes
                
                client_socket.send(resp_message)
                print(f"📤 Réponse envoyée ({len(resp_message)} octets)")
                
            except Exception as e:
                print(f"⚠️  Erreur lecture commande: {e}")
                break
                
    except Exception as e:
        print(f"❌ Erreur client: {e}")
    finally:
        client_socket.close()
        print("🔚 Client déconnecté")

def main():
    print("🧪 Serveur EPP de test - Port 8888")
    print("   Pour tester avec tunnel: modifier python_tunnel.py -> remote_port=8888")
    print("   Ou directement: nc localhost 8888")
    print("")
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('localhost', 8888))
    server.listen(5)
    
    print("🚀 Serveur en écoute sur localhost:8888")
    
    try:
        while True:
            client, addr = server.accept()
            thread = threading.Thread(target=handle_client, args=(client,))
            thread.daemon = True
            thread.start()
    except KeyboardInterrupt:
        print("\n🛑 Arrêt du serveur...")
    finally:
        server.close()

if __name__ == "__main__":
    main()
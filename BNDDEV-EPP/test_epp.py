#!/usr/bin/env python3
"""Script de test EPP minimal pour diagnostiquer la connexion"""

import ssl
import socket
import struct
import sys

def test_epp_connection(server, port):
    try:
        print(f"🔌 Test connexion TCP vers {server}:{port}...")
        
        # Test connexion TCP simple
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((server, port))
        print("✅ Connexion TCP OK")
        
        # Test handshake SSL
        print("🔐 Démarrage handshake SSL...")
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        context.set_ciphers('DEFAULT:@SECLEVEL=0')
        
        ssl_sock = context.wrap_socket(sock, server_hostname=server)
        print("✅ Handshake SSL OK")
        
        # Lecture du greeting EPP (4 octets longueur + XML)
        print("📩 Lecture du greeting EPP...")
        length_bytes = ssl_sock.recv(4)
        if len(length_bytes) != 4:
            print("❌ Impossible de lire la longueur du message")
            return False
            
        length = struct.unpack('>I', length_bytes)[0] - 4
        print(f"📏 Longueur du message: {length} octets")
        
        xml_data = b''
        while len(xml_data) < length:
            chunk = ssl_sock.recv(length - len(xml_data))
            if not chunk:
                print("❌ Connexion fermée par le serveur")
                return False
            xml_data += chunk
            
        greeting = xml_data.decode('utf-8')
        print("✅ Greeting reçu:")
        print(greeting[:200] + "..." if len(greeting) > 200 else greeting)
        
        ssl_sock.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python test_epp.py <server> <port>")
        sys.exit(1)
    
    server = sys.argv[1]
    port = int(sys.argv[2])
    
    success = test_epp_connection(server, port)
    if success:
        print("\n🎉 Test réussi ! Le serveur EPP fonctionne.")
    else:
        print("\n❌ Test échoué.")
        sys.exit(1)
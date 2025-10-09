#!/usr/bin/env python3
"""
Script pour envoyer des commandes EPP via le tunnel local port 7777
"""
import socket
import struct
import sys

def send_epp_to_tunnel(xml_command, port=7777):
    """Envoie une commande EPP au tunnel local avec format binaire correct"""
    try:
        # Connexion au tunnel local
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('localhost', port))
        
        # Format binaire EPP : 4 bytes length + XML
        xml_bytes = xml_command.encode('utf-8')
        length = len(xml_bytes) + 4
        length_bytes = struct.pack('>I', length)
        
        # Envoi
        message = length_bytes + xml_bytes
        sock.send(message)
        print(f"📤 Envoyé {length} octets")
        
        # Lecture réponse
        resp_length_bytes = sock.recv(4)
        if len(resp_length_bytes) == 4:
            resp_length = struct.unpack('>I', resp_length_bytes)[0] - 4
            response = sock.recv(resp_length).decode('utf-8')
            print(f"📥 Réponse ({resp_length} octets):")
            print(response)
        
        sock.close()
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 send_to_tunnel.py login")
        print("  python3 send_to_tunnel.py 'domain:info example.com'")
        print("  python3 send_to_tunnel.py '<epp>...</epp>'")
        return
    
    command = sys.argv[1]
    
    # Templates EPP
    if command == "login":
        xml = '''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<epp xmlns="urn:ietf:params:xml:ns:epp-1.0">
<command>
<login>
<clID>e01290</clID>
<pw>4FMPEL66sa</pw>
<options><version>1.0</version><lang>en</lang></options>
<svcs>
<objURI>urn:ietf:params:xml:ns:domain-1.0</objURI>
<objURI>urn:ietf:params:xml:ns:contact-1.0</objURI>
<objURI>urn:ietf:params:xml:ns:host-1.0</objURI>
</svcs>
</login>
<clTRID>TUNNEL-LOGIN</clTRID>
</command>
</epp>'''
    elif command.startswith("domain:info"):
        parts = command.split()
        domain = parts[1] if len(parts) > 1 else "xn--j11av3u.xn--hxt814e"
        xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<epp xmlns="urn:ietf:params:xml:ns:epp-1.0">
<command>
<info>
<domain:info xmlns:domain="urn:ietf:params:xml:ns:domain-1.0">
<domain:name>{domain}</domain:name>
</domain:info>
</info>
<clTRID>TUNNEL-DOMINFO</clTRID>
</command>
</epp>'''
    elif command == "logout":
        xml = '''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<epp xmlns="urn:ietf:params:xml:ns:epp-1.0">
<command>
<logout/>
<clTRID>TUNNEL-LOGOUT</clTRID>
</command>
</epp>'''
    else:
        # XML direct
        xml = command
    
    print(f"🚀 Envoi via tunnel local port 7777")
    send_epp_to_tunnel(xml)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Script EPP automatique avec gestion correcte du protocole binaire
"""
import ssl
import socket
import struct
import time

SERVER = "epp.gtld.knet.cn"
PORT = 700
CERT_FILE = "certs/epp.gtld.knet.cn.pem"

def send_epp_command(sock, xml_command, description):
    """Envoie une commande EPP avec le format binaire correct"""
    print(f"📤 {description}")
    print(f"📋 XML: {xml_command[:100]}...")
    
    # Encode XML et calcule longueur
    xml_bytes = xml_command.encode('utf-8')
    length = len(xml_bytes) + 4
    length_bytes = struct.pack('>I', length)
    
    # Envoie longueur + XML
    sock.send(length_bytes + xml_bytes)
    print(f"✅ Envoyé ({length} octets)")
    
    # Lit réponse
    resp_length_bytes = sock.recv(4)
    if len(resp_length_bytes) == 4:
        resp_length = struct.unpack('>I', resp_length_bytes)[0] - 4
        resp_xml = sock.recv(resp_length).decode('utf-8')
        print(f"📥 Réponse reçue:")
        print(resp_xml)
        print("-" * 60)
        return resp_xml
    return None

def main():
    print("🔌 Connexion EPP automatique...")
    
    try:
        # Configuration SSL identique au script Python principal
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        context.set_ciphers('DEFAULT:@SECLEVEL=0')
        context.options |= ssl.OP_LEGACY_SERVER_CONNECT
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.maximum_version = ssl.TLSVersion.TLSv1_2
        
        # Charge certificat client
        context.load_cert_chain(CERT_FILE, CERT_FILE)
        print("✅ Certificat client chargé")
        
        # Connexion
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(15)
        sock.connect((SERVER, PORT))
        ssl_sock = context.wrap_socket(sock, server_hostname=SERVER)
        print("✅ Connexion SSL établie")
        
        # Lit greeting
        print("📡 Lecture greeting...")
        greeting_length = struct.unpack('>I', ssl_sock.recv(4))[0] - 4
        greeting = ssl_sock.recv(greeting_length).decode('utf-8')
        print("📩 Greeting reçu:")
        print(greeting)
        print("-" * 60)
        
        # Séquence de commandes
        login_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="no"?><epp xmlns="urn:ietf:params:xml:ns:epp-1.0"><command><login><clID>e01290</clID><pw>4FMPEL66sa</pw><options><version>1.0</version><lang>en</lang></options><svcs><objURI>urn:ietf:params:xml:ns:domain-1.0</objURI><objURI>urn:ietf:params:xml:ns:contact-1.0</objURI><objURI>urn:ietf:params:xml:ns:host-1.0</objURI></svcs></login><clTRID>CLI-LOGIN-AUTO</clTRID></command></epp>'''
        
        dominfo_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="no"?><epp xmlns="urn:ietf:params:xml:ns:epp-1.0"><command><info><domain:info xmlns:domain="urn:ietf:params:xml:ns:domain-1.0"><domain:name>xn--j11av3u.xn--hxt814e</domain:name></domain:info></info><clTRID>CLI-DOMINFO-AUTO</clTRID></command></epp>'''
        
        logout_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="no"?><epp xmlns="urn:ietf:params:xml:ns:epp-1.0"><command><logout/><clTRID>CLI-LOGOUT-AUTO</clTRID></command></epp>'''
        
        # 1. LOGIN
        login_resp = send_epp_command(ssl_sock, login_xml, "LOGIN")
        if "1000" in login_resp:
            print("✅ LOGIN réussi!")
            
            # 2. DOMAIN:INFO
            dominfo_resp = send_epp_command(ssl_sock, dominfo_xml, "DOMAIN:INFO xn--j11av3u.xn--hxt814e")
            
            # 3. LOGOUT
            send_epp_command(ssl_sock, logout_xml, "LOGOUT")
        else:
            print("❌ LOGIN échoué!")
        
        ssl_sock.close()
        print("🎉 Séquence EPP terminée!")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    main()
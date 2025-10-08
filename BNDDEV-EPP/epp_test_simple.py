#!/usr/bin/env python3
"""
Test EPP minimal - juste LOGIN et vérification
"""
import ssl
import socket
import struct
import sys

def connect_epp():
    """Connexion EPP avec configuration SSL optimisée"""
    try:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        context.set_ciphers('DEFAULT:@SECLEVEL=0')
        context.options |= ssl.OP_LEGACY_SERVER_CONNECT
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.maximum_version = ssl.TLSVersion.TLSv1_2
        
        # Charge certificat
        context.load_cert_chain("certs/epp.gtld.knet.cn.pem", "certs/epp.gtld.knet.cn.pem")
        
        # Connexion
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect(("epp.gtld.knet.cn", 700))
        ssl_sock = context.wrap_socket(sock, server_hostname="epp.gtld.knet.cn")
        
        print("✅ Connexion SSL établie")
        return ssl_sock
        
    except Exception as e:
        print(f"❌ Erreur connexion: {e}")
        return None

def read_epp_message(sock):
    """Lit un message EPP (longueur + XML)"""
    try:
        # Lit les 4 premiers octets (longueur)
        length_bytes = sock.recv(4)
        if len(length_bytes) != 4:
            return None
            
        length = struct.unpack('>I', length_bytes)[0] - 4
        print(f"📏 Longueur message: {length} octets")
        
        # Lit le XML
        xml_data = b""
        while len(xml_data) < length:
            chunk = sock.recv(length - len(xml_data))
            if not chunk:
                break
            xml_data += chunk
            
        return xml_data.decode('utf-8')
        
    except Exception as e:
        print(f"❌ Erreur lecture: {e}")
        return None

def send_epp_message(sock, xml):
    """Envoie un message EPP avec format binaire"""
    try:
        xml_bytes = xml.encode('utf-8')
        length = len(xml_bytes) + 4
        length_bytes = struct.pack('>I', length)
        
        sock.send(length_bytes + xml_bytes)
        print(f"📤 Message envoyé ({length} octets)")
        return True
        
    except Exception as e:
        print(f"❌ Erreur envoi: {e}")
        return False

def main():
    print("🚀 Test EPP simple...")
    
    # Connexion
    sock = connect_epp()
    if not sock:
        return
    
    # Lit greeting
    print("📡 Lecture greeting...")
    greeting = read_epp_message(sock)
    if greeting:
        print("📩 Greeting:")
        print(greeting[:200] + "..." if len(greeting) > 200 else greeting)
        
        # Test LOGIN simple
        login_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<epp xmlns="urn:ietf:params:xml:ns:epp-1.0">
<command>
<login>
<clID>e01290</clID>
<pw>4FMPEL66sa</pw>
<options>
<version>1.0</version>
<lang>en</lang>
</options>
<svcs>
<objURI>urn:ietf:params:xml:ns:domain-1.0</objURI>
<objURI>urn:ietf:params:xml:ns:contact-1.0</objURI>
<objURI>urn:ietf:params:xml:ns:host-1.0</objURI>
</svcs>
</login>
<clTRID>CLI-TEST-LOGIN</clTRID>
</command>
</epp>'''

        print("\n🔑 Test LOGIN...")
        if send_epp_message(sock, login_xml):
            response = read_epp_message(sock)
            if response:
                print("📥 Réponse LOGIN:")
                print(response)
                
                if "1000" in response:
                    print("✅ LOGIN réussi!")
                else:
                    print("❌ LOGIN échoué")
    
    sock.close()
    print("🎯 Test terminé")

if __name__ == "__main__":
    main()
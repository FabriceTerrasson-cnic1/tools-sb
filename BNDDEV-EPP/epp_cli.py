#!/usr/bin/env python3
"""
EPP CLI - Script minimal pour tester des commandes EPP
Usage: python epp_cli.py [--server epp.example.com] [--port 700] [--cert client.pem] [--key client.key]
"""

import ssl
import socket
import struct
import xml.etree.ElementTree as ET
import argparse
import sys
from datetime import datetime

# Configuration par défaut (à adapter selon vos besoins)
DEFAULT_LOGIN = "e01290"
DEFAULT_PASSWORD = "4FMPEL66sa"
DEFAULT_CLID = "e01290"

class EPPClient:
    def __init__(self, server, port=700, cert_file=None, key_file=None):
        self.server = server
        self.port = port
        self.cert_file = cert_file
        self.key_file = key_file
        self.socket = None
        self.connected = False

    def connect(self):
        """Établit la connexion TLS avec le serveur EPP"""
        try:
            print(f"🔌 Démarrage connexion vers {self.server}:{self.port}...")
            
            # Création du socket SSL avec paramètres identiques à OpenSSL qui fonctionne
            print("🔧 Configuration du contexte SSL...")
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            # Paramètres identiques à OpenSSL: -cipher 'DEFAULT:@SECLEVEL=0' -legacy_renegotiation
            context.set_ciphers('DEFAULT:@SECLEVEL=0')
            context.options |= ssl.OP_LEGACY_SERVER_CONNECT
            
            # Force TLS 1.2 comme observé dans OpenSSL
            context.minimum_version = ssl.TLSVersion.TLSv1_2
            context.maximum_version = ssl.TLSVersion.TLSv1_2
            
            print("✅ Contexte SSL configuré")
            
            if self.cert_file:
                print(f"📜 Chargement certificat client: {self.cert_file}")
                try:
                    context.load_cert_chain(self.cert_file, self.cert_file)
                    print("✅ Certificat client chargé avec succès")
                except Exception as cert_err:
                    print(f"❌ Erreur chargement certificat: {cert_err}")
                    return False
            
            # Création socket TCP
            print("🌐 Création socket TCP...")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(15)
            
            # Connexion TCP d'abord
            print(f"� Connexion TCP vers {self.server}:{self.port}...")
            sock.connect((self.server, self.port))
            print("✅ Connexion TCP établie")
            
            # Handshake SSL
            print("🔐 Démarrage handshake SSL/TLS...")
            self.socket = context.wrap_socket(sock, server_hostname=self.server)
            print("✅ Handshake SSL/TLS réussi")
            
            # Affichage infos SSL (comme OpenSSL)
            cipher = self.socket.cipher()
            if cipher:
                print(f"🔒 Cipher utilisé: {cipher[0]}")
                print(f"📋 Protocole: {cipher[1]}")
                print(f"🔑 Bits: {cipher[2]}")
            
            print("📡 Attente du greeting EPP...")
            
            # Lire le greeting EPP
            print("✅ Connexion SSL établie avec succès!")
            greeting = self._read_epp_message()
            print("\n" + "="*60)
            print("📩 GREETING EPP REÇU:")
            print("-" * 60)
            self._print_xml_formatted(greeting)
            print("-" * 60)
            
            self.connected = True
            print("🎉 Connexion EPP complète!")
            return True
            
        except Exception as e:
            print(f"❌ Erreur de connexion: {e}")
            return False

    def login(self, login=None, password=None, clid=None):
        """Effectue l'authentification EPP"""
        if not self.connected:
            print("❌ Pas de connexion établie")
            return False
            
        login = login or DEFAULT_LOGIN
        password = password or DEFAULT_PASSWORD
        clid = clid or DEFAULT_CLID
        
        login_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<epp xmlns="urn:ietf:params:xml:ns:epp-1.0">
  <command>
    <login>
      <clID>{login}</clID>
      <pw>{password}</pw>
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
    <clTRID>{self._generate_clTRID()}</clTRID>
  </command>
</epp>"""
        
        print("🔐 Authentification en cours...")
        return self._send_command(login_xml)

    def send_custom_command(self, xml_command):
        """Envoie une commande XML personnalisée"""
        if not self.connected:
            print("❌ Pas de connexion établie")
            return False
        
        return self._send_command(xml_command)

    def hello(self):
        """Envoie une commande hello EPP"""
        hello_xml = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<epp xmlns="urn:ietf:params:xml:ns:epp-1.0">
  <hello/>
</epp>"""
        return self._send_command(hello_xml)

    def domain_info(self, domain_name):
        """Envoie une commande domain:info EPP"""
        domain_info_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<epp xmlns="urn:ietf:params:xml:ns:epp-1.0">
  <command>
    <info>
      <domain:info xmlns:domain="urn:ietf:params:xml:ns:domain-1.0">
        <domain:name>{domain_name}</domain:name>
      </domain:info>
    </info>
    <clTRID>{self._generate_clTRID()}</clTRID>
  </command>
</epp>"""
        return self._send_command(domain_info_xml)

    def logout(self):
        """Déconnexion EPP"""
        logout_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<epp xmlns="urn:ietf:params:xml:ns:epp-1.0">
  <command>
    <logout/>
    <clTRID>{self._generate_clTRID()}</clTRID>
  </command>
</epp>"""
        
        print("👋 Déconnexion...")
        result = self._send_command(logout_xml)
        self.disconnect()
        return result

    def disconnect(self):
        """Ferme la connexion"""
        if self.socket:
            self.socket.close()
            self.connected = False
            print("🔌 Connexion fermée")

    def _send_command(self, xml_command):
        """Envoie une commande EPP et traite la réponse"""
        try:
            print("\n" + "="*60)
            print("📤 COMMANDE XML ENVOYÉE:")
            print("-" * 60)
            self._print_xml_formatted(xml_command)
            print("-" * 60)
            
            # Envoie la commande
            self._write_epp_message(xml_command)
            
            # Lit la réponse
            response = self._read_epp_message()
            print("\n📥 RÉPONSE XML REÇUE:")
            print("-" * 60)
            self._print_xml_formatted(response)
            print("-" * 60)
            
            # Analyse le code de résultat
            self._analyze_response(response)
            print("="*60)
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de l'envoi: {e}")
            return False

    def _read_epp_message(self):
        """Lit un message EPP (4 octets de longueur + XML)"""
        # Lire la longueur du message (4 octets, big-endian)
        length_bytes = self.socket.recv(4)
        if len(length_bytes) != 4:
            raise Exception("Impossible de lire la longueur du message")
        
        length = struct.unpack('>I', length_bytes)[0] - 4
        
        # Lire le message XML
        xml_data = b''
        while len(xml_data) < length:
            chunk = self.socket.recv(length - len(xml_data))
            if not chunk:
                raise Exception("Connexion fermée par le serveur")
            xml_data += chunk
        
        return xml_data.decode('utf-8')

    def _write_epp_message(self, xml_message):
        """Écrit un message EPP (4 octets de longueur + XML)"""
        xml_bytes = xml_message.encode('utf-8')
        length = len(xml_bytes) + 4
        length_bytes = struct.pack('>I', length)
        
        self.socket.send(length_bytes + xml_bytes)

    def _print_xml(self, xml_string):
        """Affiche le XML de façon lisible"""
        try:
            root = ET.fromstring(xml_string)
            # Formatage basique pour l'affichage
            print("  " + xml_string.replace('\n', '\n  '))
        except:
            print("  " + xml_string)
        print()

    def _print_xml_formatted(self, xml_string):
        """Affiche le XML avec formatage amélioré"""
        try:
            import xml.dom.minidom
            dom = xml.dom.minidom.parseString(xml_string)
            formatted = dom.toprettyxml(indent="  ")
            # Supprimer les lignes vides
            lines = [line for line in formatted.split('\n') if line.strip()]
            for line in lines[1:]:  # Skip la première ligne <?xml ...?>
                print(line)
        except:
            # Fallback vers affichage simple
            print(xml_string)
        print()

    def _analyze_response(self, xml_response):
        """Analyse la réponse EPP et affiche le résultat"""
        try:
            root = ET.fromstring(xml_response)
            
            # Cherche le code de résultat
            result = root.find('.//{urn:ietf:params:xml:ns:epp-1.0}result')
            if result is not None:
                code = result.get('code')
                msg = result.find('.//{urn:ietf:params:xml:ns:epp-1.0}msg')
                message = msg.text if msg is not None else "Pas de message"
                
                # Classification des codes EPP
                if code.startswith('1'):
                    status = "✅ SUCCÈS"
                elif code.startswith('2'):
                    status = "🎯 SUCCÈS (avec info)"
                else:
                    status = "❌ ERREUR"
                
                print(f"📊 Résultat: {status} - Code {code}: {message}")
                
        except Exception as e:
            print(f"⚠️  Impossible d'analyser la réponse: {e}")

    def _generate_clTRID(self):
        """Génère un ID de transaction client"""
        return f"CLI-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

def main():
    parser = argparse.ArgumentParser(description="CLI EPP minimal")
    parser.add_argument("--server", required=True, help="Serveur EPP (ex: epp.example.com)")
    parser.add_argument("--port", type=int, default=700, help="Port EPP (défaut: 700)")
    parser.add_argument("--cert", help="Fichier certificat client (.pem)")
    parser.add_argument("--key", help="Fichier clé privée (.key)")
    parser.add_argument("--login", help="Login EPP (sinon utilise la constante)")
    parser.add_argument("--password", help="Mot de passe EPP (sinon utilise la constante)")
    parser.add_argument("--clid", help="Client ID EPP (sinon utilise la constante)")
    parser.add_argument("--domain", help="Domaine pour commande domain:info")
    
    args = parser.parse_args()
    
    # Création du client EPP
    client = EPPClient(args.server, args.port, args.cert, args.key)
    
    try:
        # Connexion
        if not client.connect():
            sys.exit(1)
        
        # Authentification
        if not client.login(args.login, args.password, args.clid):
            sys.exit(1)
        
        # Si un domaine est spécifié, faire domain:info et sortir
        if args.domain:
            print(f"\n🔍 Requête domain:info pour: {args.domain}")
            client.domain_info(args.domain)
            client.logout()
            return
        
        print("\n🎉 Connexion EPP établie ! Commandes disponibles:")
        print("  'hello' - Envoie une commande hello")
        print("  'domain:info <domaine>' - Informations sur un domaine")
        print("  'logout' - Se déconnecter")
        print("  'xml:<votre_xml>' - Envoie du XML personnalisé")
        print("  'quit' - Quitter sans logout")
        print()
        
        # Boucle interactive
        while True:
            try:
                cmd = input("EPP> ").strip()
                
                if cmd == 'quit':
                    break
                elif cmd == 'logout':
                    client.logout()
                    break
                elif cmd == 'hello':
                    client.hello()
                elif cmd.startswith('domain:info '):
                    domain_name = cmd[12:].strip()
                    if domain_name:
                        client.domain_info(domain_name)
                    else:
                        print("❌ Veuillez spécifier un nom de domaine")
                elif cmd.startswith('xml:'):
                    custom_xml = cmd[4:].strip()
                    client.send_custom_command(custom_xml)
                elif cmd == '':
                    continue
                else:
                    print("❓ Commande non reconnue. Utilisez 'hello', 'domain:info <domaine>', 'logout', 'xml:<xml>', ou 'quit'")
                    
            except KeyboardInterrupt:
                print("\n🛑 Interruption clavier")
                break
            except EOFError:
                print("\n👋 Au revoir!")
                break
        
    finally:
        client.disconnect()

if __name__ == "__main__":
    main()
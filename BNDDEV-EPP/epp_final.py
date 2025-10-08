#!/usr/bin/env python3
"""
EPP CLI Final - Connexion complète avec gestion d'erreurs améliorée

Usage:
  ./epp_final.py                    # Mode interactif
  ./epp_final.py domain:info example.com  # Commande directe
  ./epp_final.py auto               # Séquence automatique
"""
import ssl
import socket
import struct
import sys
import time

# Codes couleur ANSI pour les messages
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_panel(title, content, border_color="blue"):
    """Simule rich.Panel avec des caractères ASCII"""
    color = getattr(Colors, border_color.upper(), Colors.BLUE)
    print(f"\n{color}╭─── {title} ───╮{Colors.END}")
    for line in content.split('\n'):
        print(f"{color}│{Colors.END} {line}")
    print(f"{color}╰{'─' * (len(title) + 8)}╯{Colors.END}")

def print_box(text):
    """Simule Panel.fit pour les titres"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}╭{'─' * (len(text) + 2)}╮{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}│ {text} │{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}╰{'─' * (len(text) + 2)}╯{Colors.END}")

class EPPClient:
    def __init__(self, server="epp.gtld.knet.cn", port=700, cert_file="certs/epp.gtld.knet.cn.pem"):
        self.server = server
        self.port = port
        self.cert_file = cert_file
        self.sock = None
        self.connected = False
        
    def log(self, msg, style="info"):
        if style == "success":
            print(f"{Colors.GREEN}✅ {msg}{Colors.END}")
        elif style == "error":
            print(f"{Colors.RED}❌ {msg}{Colors.END}")
        elif style == "warning":
            print(f"{Colors.YELLOW}⚠️ {msg}{Colors.END}")
        else:
            print(f"{Colors.BLUE}ℹ️ {msg}{Colors.END}")
    
    def connect(self):
        """Établit la connexion EPP avec SSL"""
        try:
            self.log(f"Connexion vers {self.server}:{self.port}")
            
            # Configuration SSL optimisée
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            context.set_ciphers('DEFAULT:@SECLEVEL=0')
            context.options |= ssl.OP_LEGACY_SERVER_CONNECT
            context.minimum_version = ssl.TLSVersion.TLSv1_2
            context.maximum_version = ssl.TLSVersion.TLSv1_2
            
            # Charge certificat client
            context.load_cert_chain(self.cert_file, self.cert_file)
            self.log("Certificat client chargé")
            
            # Connexion socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(15)
            sock.connect((self.server, self.port))
            self.sock = context.wrap_socket(sock, server_hostname=self.server)
            
            self.log("Connexion SSL établie", "success")
            
            # Lit le greeting
            greeting = self.read_message()
            if greeting:
                self.log("Greeting EPP reçu", "success")
                if "KNET Co.,Ltd. EPP Server" in greeting:
                    self.connected = True
                    return True
                else:
                    self.log("Greeting invalide", "error")
                    return False
            else:
                self.log("Pas de greeting reçu", "error")
                return False
                
        except socket.timeout:
            self.log("Timeout de connexion - Vérifiez l'IP whitelisting", "error")
            return False
        except Exception as e:
            self.log(f"Erreur connexion: {e}", "error")
            return False
    
    def read_message(self):
        """Lit un message EPP (format binaire)"""
        try:
            # Lit longueur (4 octets big-endian)
            length_bytes = self.sock.recv(4)
            if len(length_bytes) != 4:
                return None
                
            length = struct.unpack('>I', length_bytes)[0] - 4
            
            # Lit XML
            xml_data = b""
            while len(xml_data) < length:
                chunk = self.sock.recv(length - len(xml_data))
                if not chunk:
                    break
                xml_data += chunk
                
            return xml_data.decode('utf-8')
            
        except Exception as e:
            self.log(f"Erreur lecture: {e}", "error")
            return None
    
    def send_command(self, xml, description=""):
        """Envoie une commande EPP"""
        try:
            if description:
                self.log(f"Envoi: {description}")
            
            # Format binaire EPP
            xml_bytes = xml.encode('utf-8')
            length = len(xml_bytes) + 4
            length_bytes = struct.pack('>I', length)
            
            self.sock.send(length_bytes + xml_bytes)
            
            # Lit réponse
            response = self.read_message()
            if response:
                return response
            else:
                self.log("Pas de réponse reçue", "error")
                return None
                
        except Exception as e:
            self.log(f"Erreur envoi: {e}", "error")
            return None
    
    def login(self, clid="e01290", password="4FMPEL66sa"):
        """Authentification EPP"""
        login_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<epp xmlns="urn:ietf:params:xml:ns:epp-1.0">
<command>
<login>
<clID>{clid}</clID>
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
<clTRID>CLI-LOGIN-{int(time.time())}</clTRID>
</command>
</epp>'''
        
        response = self.send_command(login_xml, "LOGIN")
        if response and "1000" in response:
            self.log("LOGIN réussi", "success")
            return True
        else:
            self.log("LOGIN échoué", "error")
            if response:
                print_panel("Réponse LOGIN", response, "red")
            return False
    
    def domain_info(self, domain):
        """Requête domain:info"""
        dominfo_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<epp xmlns="urn:ietf:params:xml:ns:epp-1.0">
<command>
<info>
<domain:info xmlns:domain="urn:ietf:params:xml:ns:domain-1.0">
<domain:name>{domain}</domain:name>
</domain:info>
</info>
<clTRID>CLI-DOMINFO-{int(time.time())}</clTRID>
</command>
</epp>'''
        
        response = self.send_command(dominfo_xml, f"DOMAIN:INFO {domain}")
        if response:
            print_panel(f"Info domaine: {domain}", response, "green")
            return True
        return False
    
    def logout(self):
        """Déconnexion EPP"""
        logout_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<epp xmlns="urn:ietf:params:xml:ns:epp-1.0">
<command>
<logout/>
<clTRID>CLI-LOGOUT-{int(time.time())}</clTRID>
</command>
</epp>'''
        
        response = self.send_command(logout_xml, "LOGOUT")
        if response and "1500" in response:
            self.log("LOGOUT réussi", "success")
            return True
        return False
    
    def close(self):
        """Ferme la connexion"""
        if self.sock:
            self.sock.close()
            self.connected = False

def main():
    """Fonction principale"""
    print_box("🚀 EPP CLI Final")
    
    # Vérifie les arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "auto":
            mode = "auto"
            domain = "xn--j11av3u.xn--hxt814e"
        elif sys.argv[1].startswith("domain:info"):
            mode = "dominfo"
            domain = sys.argv[2] if len(sys.argv) > 2 else "xn--j11av3u.xn--hxt814e"
        else:
            mode = "help"
    else:
        mode = "interactive"
    
    if mode == "help":
        print(f"""
{Colors.BOLD}Usage:{Colors.END}
  ./epp_final.py                    Mode interactif
  ./epp_final.py domain:info <domain>  Requête domaine
  ./epp_final.py auto               Séquence automatique
        """)
        return
    
    # Crée client EPP
    client = EPPClient()
    
    # Test de connexion
    if not client.connect():
        print(f"{Colors.RED}❌ Connexion impossible{Colors.END}")
        print(f"\n{Colors.YELLOW}Diagnostics possibles:{Colors.END}")
        print("• IP non whitelistée (doit être 109.234.107.23)")
        print("• Certificat client invalide")
        print("• Serveur indisponible")
        return
    
    try:
        # Login
        if not client.login():
            return
        
        if mode == "auto":
            # Séquence automatique
            client.domain_info("xn--j11av3u.xn--hxt814e")
            
        elif mode == "dominfo":
            client.domain_info(domain)
            
        else:
            # Mode interactif
            print(f"\n{Colors.GREEN}✅ Connecté! Tapez vos commandes:{Colors.END}")
            print("• domain:info <domaine>")
            print("• quit pour quitter")
            
            while True:
                try:
                    cmd = input("\nEPP> ").strip()
                    if cmd.lower() in ['quit', 'exit']:
                        break
                    elif cmd.startswith('domain:info'):
                        parts = cmd.split()
                        if len(parts) > 1:
                            client.domain_info(parts[1])
                        else:
                            print(f"{Colors.RED}Usage: domain:info <domaine>{Colors.END}")
                    else:
                        print(f"{Colors.YELLOW}Commande non reconnue{Colors.END}")
                        
                except KeyboardInterrupt:
                    break
        
        # Logout
        client.logout()
        
    finally:
        client.close()
    
    print(f"{Colors.BLUE}🎯 Session EPP terminée{Colors.END}")

if __name__ == "__main__":
    main()
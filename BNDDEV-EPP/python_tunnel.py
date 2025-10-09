#!/usr/bin/env python3
"""
Tunnel SSL Python personnalisé - Port 7777 -> epp.gtld.knet.cn:700
Alternative à socat qui évite les restrictions OpenSSL modernes
"""
import socket
import ssl
import threading
import sys
import signal

class SSLTunnel:
    def __init__(self, local_port=7777, remote_host="epp.gtld.knet.cn", remote_port=700, cert_file="/Users/fabrice/dev/tools-sb/BNDDEV-EPP/certs/epp.gtld.knet.cn.pem"):
        self.local_port = local_port
        self.remote_host = remote_host 
        self.remote_port = remote_port
        self.cert_file = cert_file
        self.running = False
        
    def create_ssl_context(self):
        """Crée un contexte SSL ultra-permissif"""
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        # Force les paramètres legacy les plus permissifs
        try:
            context.set_ciphers('ALL:COMPLEMENTOFALL:eNULL:@SECLEVEL=0')
        except:
            context.set_ciphers('ALL:COMPLEMENTOFALL')
            
        # Options legacy
        try:
            context.options |= ssl.OP_LEGACY_SERVER_CONNECT
            context.options |= ssl.OP_ALLOW_UNSAFE_LEGACY_RENEGOTIATION
        except:
            pass
            
        # Force TLS 1.2
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.maximum_version = ssl.TLSVersion.TLSv1_2
        
        # Charge le certificat client
        try:
            context.load_cert_chain(self.cert_file, self.cert_file)
            print(f"✅ Certificat client chargé: {self.cert_file}")
        except Exception as e:
            print(f"⚠️  Attention: Impossible de charger le certificat: {e}")
            print("   Le tunnel fonctionnera sans certificat client")
            
        return context
    
    def handle_client(self, client_socket):
        """Gère une connexion client"""
        try:
            # Connexion SSL vers le serveur distant
            ssl_context = self.create_ssl_context()
            
            # Socket vers serveur distant
            remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote_socket.settimeout(10)
            
            # Connexion SSL
            ssl_socket = ssl_context.wrap_socket(
                remote_socket, 
                server_hostname=self.remote_host,
                do_handshake_on_connect=False
            )
            
            print(f"🔌 Connexion vers {self.remote_host}:{self.remote_port}...")
            ssl_socket.connect((self.remote_host, self.remote_port))
            
            print(f"🤝 Handshake SSL...")
            ssl_socket.do_handshake()
            
            print(f"✅ Connexion SSL réussie!")
            print(f"   Cipher: {ssl_socket.cipher()}")
            
            print(f"🔗 Tunnel établi: client -> {self.remote_host}:{self.remote_port}")
            
            # Lire et afficher le greeting EPP
            try:
                print("📡 Lecture greeting EPP...")
                greeting_data = ssl_socket.recv(4096)
                if greeting_data:
                    print(f"📩 Greeting reçu ({len(greeting_data)} octets):")
                    print(greeting_data.decode('utf-8', errors='ignore')[:500])
            except Exception as e:
                print(f"⚠️  Pas de greeting immédiat: {e}")
            
            # Tunnel bidirectionnel
            self.relay_data(client_socket, ssl_socket)
            
        except Exception as e:
            print(f"❌ Erreur tunnel: {e}")
        finally:
            try:
                client_socket.close()
                ssl_socket.close()
            except:
                pass
    
    def relay_data(self, sock1, sock2):
        """Relaie les données entre deux sockets"""
        def forward(source, destination):
            try:
                while True:
                    data = source.recv(4096)
                    if not data:
                        break
                    destination.send(data)
            except:
                pass
            finally:
                try:
                    source.close()
                    destination.close()
                except:
                    pass
        
        # Threads pour relayer dans les deux directions
        t1 = threading.Thread(target=forward, args=(sock1, sock2))
        t2 = threading.Thread(target=forward, args=(sock2, sock1))
        
        t1.daemon = True
        t2.daemon = True
        
        t1.start()
        t2.start()
        
        t1.join()
        t2.join()
    
    def start(self):
        """Démarre le tunnel"""
        self.running = True
        
        # Socket d'écoute
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('localhost', self.local_port))
        server_socket.listen(5)
        
        print(f"🚀 Tunnel SSL Python démarré")
        print(f"   Écoute sur: localhost:{self.local_port}")
        print(f"   Redirige vers: {self.remote_host}:{self.remote_port}")
        print(f"   Certificat: {self.cert_file}")
        print(f"   Arrêt: Ctrl+C")
        print()
        
        try:
            while self.running:
                try:
                    client_socket, address = server_socket.accept()
                    print(f"📞 Nouvelle connexion de {address}")
                    
                    # Handle dans un thread séparé
                    client_thread = threading.Thread(
                        target=self.handle_client, 
                        args=(client_socket,)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except socket.error:
                    if self.running:
                        print("❌ Erreur socket")
                        
        except KeyboardInterrupt:
            print("\n🛑 Arrêt du tunnel...")
        finally:
            self.running = False
            server_socket.close()

def signal_handler(sig, frame):
    print("\n🛑 Signal reçu, arrêt du tunnel...")
    sys.exit(0)

def main():
    # Gestion Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    print("🐍 Tunnel SSL Python - Alternative à socat")
    print("=" * 50)
    
    # Démarre le tunnel
    tunnel = SSLTunnel()
    tunnel.start()

if __name__ == "__main__":
    main()
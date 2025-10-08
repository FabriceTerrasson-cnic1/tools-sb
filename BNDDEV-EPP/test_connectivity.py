#!/usr/bin/env python3
"""Test simple de connectivité EPP"""
import socket
import sys

def test_tcp_connection():
    try:
        print("🔌 Test connexion TCP simple...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        sock.settimeout(5)
        result = sock.connect_ex(('epp.gtld.knet.cn', 700))
        sock.close()
        
        if result == 0:
            print("✅ Connexion TCP réussie - IP whitelistée !")
            return True
        else:
            print(f"❌ Connexion TCP échouée - Code d'erreur: {result}")
            print("💡 Votre IP n'est probablement pas whitelistée")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    success = test_tcp_connection()
    if success:
        print("\n🎉 Vous pouvez maintenant lancer le script EPP !")
        print("python3 epp_cli.py --server epp.gtld.knet.cn --port 700 --cert certs/epp.gtld.knet.cn.pem --domain xn--j11av3u.xn--hxt814e")
    else:
        print("\n📋 Solutions:")
        print("1. Exécutez depuis l'IP whitelistée (109.234.107.23)")
        print("2. Utilisez un tunnel SSH:")
        print("   ssh -L 7000:epp.gtld.knet.cn:700 user@109.234.107.23")
        print("   python3 epp_cli.py --server localhost --port 7000 --cert certs/epp.gtld.knet.cn.pem --domain xn--j11av3u.xn--hxt814e")
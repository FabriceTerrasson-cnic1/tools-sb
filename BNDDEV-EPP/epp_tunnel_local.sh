#!/bin/bash
# Tunnel SSL local vers serveur EPP
# Écoute sur port 7777 local et redirige vers epp.gtld.knet.cn:700

echo "🚀 Création tunnel SSL local port 7777 -> epp.gtld.knet.cn:700"
echo "📡 Une fois connecté, vous pourrez utiliser: telnet localhost 7777"
echo "🔑 Certificats: certs/epp.gtld.knet.cn.pem"
echo ""

# Vérification des certificats
if [ ! -f "certs/epp.gtld.knet.cn.pem" ]; then
    echo "❌ Erreur: Certificat certs/epp.gtld.knet.cn.pem non trouvé"
    exit 1
fi

echo "✅ Certificat trouvé"
echo "🔌 Démarrage du tunnel SSL..."
echo "   Local:  localhost:7777"  
echo "   Remote: epp.gtld.knet.cn:700"
echo ""
echo "💡 Pour tester: telnet localhost 7777"
echo "🛑 Pour arrêter: Ctrl+C"
echo ""

# Création du tunnel avec socat
if command -v socat >/dev/null 2>&1; then
    echo "📦 Utilisation de socat pour le tunnel..."
    socat TCP-LISTEN:7777,reuseaddr,fork \
          OPENSSL:epp.gtld.knet.cn:700,cert=certs/epp.gtld.knet.cn.pem,key=certs/epp.gtld.knet.cn.pem,verify=0,method=TLSv1.2,ciphers='DEFAULT:@SECLEVEL=0'
else
    echo "❌ socat non installé. Installation..."
    echo "🍺 Installation via Homebrew:"
    echo "   brew install socat"
    echo ""
    echo "⚡ Tunnel alternatif avec netcat + OpenSSL:"
    
    # Méthode alternative avec netcat et named pipes
    PIPE1="/tmp/epp_pipe1_$$"
    PIPE2="/tmp/epp_pipe2_$$"
    
    # Nettoyage à la sortie
    cleanup() {
        echo ""
        echo "🧹 Nettoyage..."
        rm -f "$PIPE1" "$PIPE2"
        echo "✅ Tunnel fermé"
        exit 0
    }
    trap cleanup EXIT INT TERM
    
    # Création des pipes
    mkfifo "$PIPE1" "$PIPE2"
    
    echo "🔧 Tunnel avec netcat + OpenSSL..."
    echo "📡 En attente de connexions sur localhost:7777..."
    
    while true; do
        # Accepte connexion locale et la redirige vers OpenSSL
        nc -l 7777 <"$PIPE1" | \
        openssl s_client -connect epp.gtld.knet.cn:700 \
                        -cert certs/epp.gtld.knet.cn.pem \
                        -key certs/epp.gtld.knet.cn.pem \
                        -tls1_2 \
                        -cipher 'DEFAULT:@SECLEVEL=0' \
                        -legacy_server_connect \
                        -quiet >"$PIPE1"
        
        echo "🔄 Connexion fermée, en attente de nouvelle connexion..."
        sleep 1
    done
fi
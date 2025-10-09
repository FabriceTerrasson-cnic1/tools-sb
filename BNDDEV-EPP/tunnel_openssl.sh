#!/bin/bash
# Tunnel SSL alternatif avec OpenSSL s_client en background
# Port local 7777 -> epp.gtld.knet.cn:700

echo "🚀 Tunnel SSL alternatif (OpenSSL)"
echo "   Local:  localhost:7777" 
echo "   Remote: epp.gtld.knet.cn:700"
echo ""

# Fonction pour gérer une connexion
handle_connection() {
    local port=$1
    echo "📡 Nouvelle connexion sur port $port"
    
    # Pipe bidirectionnel entre netcat local et openssl distant
    mkfifo /tmp/tunnel_$port 2>/dev/null || true
    
    # OpenSSL vers serveur distant
    openssl s_client -connect epp.gtld.knet.cn:700 \
        -cert certs/epp.gtld.knet.cn.pem \
        -key certs/epp.gtld.knet.cn.pem \
        -tls1_2 -cipher 'DEFAULT:@SECLEVEL=0' \
        -legacy_server_connect -quiet \
        < /tmp/tunnel_$port | nc -l $port > /tmp/tunnel_$port &
    
    local ssl_pid=$!
    
    # Nettoie quand terminé
    wait $ssl_pid
    rm -f /tmp/tunnel_$port
    echo "🔚 Connexion $port terminée"
}

echo "💡 Utilisation:"
echo "   echo 'test' | nc localhost 7777"
echo "   nc localhost 7777  (mode interactif)"
echo ""
echo "⚠️  Note: Chaque connexion crée un nouveau tunnel SSL"
echo "🛑 Ctrl+C pour arrêter"
echo ""

# Boucle d'écoute simple
while true; do
    echo "👂 Écoute sur port 7777..."
    handle_connection 7777
    sleep 1
done
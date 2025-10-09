#!/bin/bash
# Tunnel OpenSSL bidirectionnel - Port 7777 -> EPP Server
# Utilise openssl s_client qui fonctionne, contrairement à socat OPENSSL

echo "🚀 Tunnel OpenSSL - Port 7777 -> epp.gtld.knet.cn:700"
echo "   Utilise: openssl s_client (testé et fonctionnel)"
echo "   Usage: nc localhost 7777"
echo "   Arrêt: Ctrl+C"
echo ""

# Crée des pipes nommés pour la communication bidirectionnelle
PIPE_TO_SERVER="/tmp/epp_to_server_$$"
PIPE_TO_CLIENT="/tmp/epp_to_client_$$"

# Nettoie les pipes au démarrage et à l'arrêt
cleanup() {
    echo "🧹 Nettoyage..."
    rm -f "$PIPE_TO_SERVER" "$PIPE_TO_CLIENT"
    pkill -P $$ 2>/dev/null
    exit 0
}
trap cleanup EXIT INT TERM

# Crée les pipes nommés
mkfifo "$PIPE_TO_SERVER" "$PIPE_TO_CLIENT" 2>/dev/null

echo "🔧 Pipes créés: $PIPE_TO_SERVER, $PIPE_TO_CLIENT"

# Démarre openssl s_client en arrière-plan avec connexion permanente
echo "🔌 Démarrage connexion SSL vers epp.gtld.knet.cn:700..."
openssl s_client -connect epp.gtld.knet.cn:700 \
    -cert certs/epp.gtld.knet.cn.pem \
    -key certs/epp.gtld.knet.cn.pem \
    -tls1_2 -cipher 'DEFAULT:@SECLEVEL=0' \
    -legacy_server_connect -quiet \
    < "$PIPE_TO_SERVER" > "$PIPE_TO_CLIENT" &

SSL_PID=$!
echo "✅ OpenSSL PID: $SSL_PID"

# Attendre que la connexion SSL soit établie
sleep 2

# Démarre le serveur local avec socat qui utilise les pipes
echo "👂 Écoute sur localhost:7777..."
socat TCP-LISTEN:7777,reuseaddr,fork \
    SYSTEM:"cat > $PIPE_TO_SERVER & cat < $PIPE_TO_CLIENT; wait" &

SOCAT_PID=$!
echo "✅ Socat PID: $SOCAT_PID"

echo ""
echo "🎯 Tunnel prêt! Test avec:"
echo "   nc localhost 7777"
echo "   echo 'test' | nc localhost 7777"
echo ""

# Attendre que les processus se terminent
wait
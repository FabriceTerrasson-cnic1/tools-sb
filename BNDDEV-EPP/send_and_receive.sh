#!/bin/bash
# Script pour envoyer une commande et voir la réponse complète

if [ $# -eq 0 ]; then
    echo "Usage: ./send_and_receive.sh 'votre commande'"
    echo "Exemple: ./send_and_receive.sh 'test'"
    exit 1
fi

COMMAND="$1"
PORT=7777

echo "📤 Envoi vers localhost:$PORT"
echo "💬 Commande: $COMMAND"
echo "───────────────────────────"

# Méthode 1: Avec expect pour capturer la réponse
if command -v expect &> /dev/null; then
    expect << EOF
spawn socat - TCP:localhost:$PORT
send "$COMMAND\r"
expect {
    timeout { puts "Timeout - pas de réponse"; exit 1 }
    eof { exit 0 }
    -re ".*" { puts \$expect_out(buffer); exp_continue }
}
EOF
else
    # Méthode 2: Avec timeout et redirection
    {
        echo "$COMMAND"
        sleep 3  # Attendre la réponse
    } | timeout 10s socat - TCP:localhost:$PORT
fi

echo ""
echo "✅ Terminé"
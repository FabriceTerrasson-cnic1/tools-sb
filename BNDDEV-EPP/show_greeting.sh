#!/bin/bash
# Script pour se connecter au tunnel EPP et afficher proprement les réponses

PORT=${1:-7777}
HOST=${2:-localhost}

echo "🔌 Connexion au tunnel EPP sur $HOST:$PORT"
echo "📡 En attente du greeting EPP..."
echo "════════════════════════════════════════════════════"

# Utilise nc avec timeout pour capturer la réponse
{
    # Envoie une connexion et attend la réponse
    sleep 1
} | nc -w 5 $HOST $PORT | {
    # Traite la réponse ligne par ligne
    echo "📥 GREETING EPP REÇU :"
    echo "──────────────────────"
    
    # Affiche le XML formaté
    while IFS= read -r line; do
        # Supprime les caractères de contrôle au début
        clean_line=$(echo "$line" | sed 's/^x//')
        
        # Formate le XML pour une meilleure lisibilité
        if [[ "$clean_line" == *"<?xml"* ]]; then
            echo "📄 $clean_line"
        elif [[ "$clean_line" == *"<epp"* ]]; then
            echo "🏷️  $clean_line"
        elif [[ "$clean_line" == *"<greeting>"* ]]; then
            echo "👋 $clean_line"
        elif [[ "$clean_line" == *"<svID>"* ]]; then
            echo "🖥️  $clean_line"
        elif [[ "$clean_line" == *"<svDate>"* ]]; then
            echo "📅 $clean_line"
        else
            echo "   $clean_line"
        fi
    done
    
    echo "──────────────────────"
    echo "✅ Greeting EPP terminé"
}

echo ""
echo "💡 Pour une session interactive :"
echo "   nc $HOST $PORT"
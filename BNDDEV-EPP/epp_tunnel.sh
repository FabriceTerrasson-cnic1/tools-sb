#!/bin/bash
# Script EPP automatique avec format binaire correct

SERVER="epp.gtld.knet.cn"
PORT="700"
CERT="certs/epp.gtld.knet.cn.pem"

echo "🔌 Connexion EPP automatique vers $SERVER:$PORT"
echo "📜 Certificat client: $CERT"
echo "🤖 Envoi automatique: GREETING → LOGIN → DOMAIN:INFO"
echo ""

# Fonction pour calculer la longueur EPP (4 octets big-endian + XML)
function send_epp_command() {
    local xml="$1"
    local length=$((${#xml} + 4))
    
    echo "📤 Envoi commande EPP (longueur: $length octets)"
    echo "� XML: $xml"
    
    # Conversion longueur en 4 octets big-endian + XML
    python3 -c "
import struct
import sys
xml = '''$xml'''
length = len(xml.encode('utf-8')) + 4
length_bytes = struct.pack('>I', length)
sys.stdout.buffer.write(length_bytes)
sys.stdout.buffer.write(xml.encode('utf-8'))
sys.stdout.buffer.flush()
"
}

# Commandes EPP
LOGIN_XML='<?xml version="1.0" encoding="UTF-8" standalone="no"?><epp xmlns="urn:ietf:params:xml:ns:epp-1.0"><command><login><clID>e01290</clID><pw>4FMPEL66sa</pw><options><version>1.0</version><lang>en</lang></options><svcs><objURI>urn:ietf:params:xml:ns:domain-1.0</objURI><objURI>urn:ietf:params:xml:ns:contact-1.0</objURI><objURI>urn:ietf:params:xml:ns:host-1.0</objURI></svcs></login><clTRID>CLI-LOGIN-AUTO</clTRID></command></epp>'

DOMINFO_XML='<?xml version="1.0" encoding="UTF-8" standalone="no"?><epp xmlns="urn:ietf:params:xml:ns:epp-1.0"><command><info><domain:info xmlns:domain="urn:ietf:params:xml:ns:domain-1.0"><domain:name>xn--j11av3u.xn--hxt814e</domain:name></domain:info></info><clTRID>CLI-DOMINFO-AUTO</clTRID></command></epp>'

LOGOUT_XML='<?xml version="1.0" encoding="UTF-8" standalone="no"?><epp xmlns="urn:ietf:params:xml:ns:epp-1.0"><command><logout/><clTRID>CLI-LOGOUT-AUTO</clTRID></command></epp>'

echo "🚀 Démarrage séquence EPP automatique..."

# Connexion et envoi des commandes
(
    echo "📡 Attente greeting..."
    sleep 2
    
    echo "🔐 Envoi LOGIN..."
    send_epp_command "$LOGIN_XML"
    sleep 1
    
    echo "🔍 Envoi DOMAIN:INFO..."
    send_epp_command "$DOMINFO_XML" 
    sleep 1
    
    echo "👋 Envoi LOGOUT..."
    send_epp_command "$LOGOUT_XML"
    sleep 1
    
) | openssl s_client -connect $SERVER:$PORT \
    -cert $CERT \
    -key $CERT \
    -legacy_renegotiation \
    -cipher 'DEFAULT:@SECLEVEL=0' \
    -quiet

echo ""
echo "✅ Séquence EPP terminée"
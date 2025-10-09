#!/bin/bash
# Test automatique des ciphers contre le serveur EPP

SERVER="epp.gtld.knet.cn:700"
CERT="certs/epp.gtld.knet.cn.pem"

echo "🔍 Test des ciphers supportés par $SERVER"
echo "═══════════════════════════════════════════════"

# Test des groupes de ciphers principaux
cipher_groups=(
    "HIGH:@SECLEVEL=0"
    "MEDIUM:@SECLEVEL=0" 
    "LOW:@SECLEVEL=0"
    "ALL:@SECLEVEL=0"
    "DEFAULT:@SECLEVEL=0"
    "COMPLEMENTOFALL:@SECLEVEL=0"
    "eNULL:@SECLEVEL=0"
)

for group in "${cipher_groups[@]}"; do
    echo -n "🧪 Testing cipher group '$group': "
    
    result=$(timeout 10 openssl s_client -connect $SERVER \
        -cert $CERT -key $CERT \
        -tls1_2 -cipher "$group" \
        -legacy_server_connect -quiet 2>&1 </dev/null)
    
    if echo "$result" | grep -q "BEGIN CERTIFICATE\|<epp"; then
        cipher=$(echo "$result" | grep "Cipher is" | cut -d' ' -f3)
        echo "✅ OK - Cipher: $cipher"
    else
        echo "❌ FAILED"
        # echo "   Error: $(echo "$result" | head -1)"
    fi
done

echo ""
echo "🔍 Test des ciphers individuels les plus courants..."
echo "═══════════════════════════════════════════════════"

# Ciphers spécifiques à tester
specific_ciphers=(
    "AES256-GCM-SHA384"
    "AES128-GCM-SHA256"
    "AES256-SHA256"
    "AES128-SHA256"
    "AES256-SHA"
    "AES128-SHA"
    "DES-CBC3-SHA"
    "RC4-SHA"
    "RC4-MD5"
)

for cipher in "${specific_ciphers[@]}"; do
    echo -n "🧪 Testing '$cipher': "
    
    result=$(timeout 5 openssl s_client -connect $SERVER \
        -cert $CERT -key $CERT \
        -tls1_2 -cipher "$cipher" \
        -legacy_server_connect -quiet 2>&1 </dev/null)
    
    if echo "$result" | grep -q "BEGIN CERTIFICATE\|<epp"; then
        echo "✅ OK"
    else
        echo "❌ FAILED"
    fi
done

echo ""
echo "💡 Pour utiliser avec socat, essayez:"
echo "   socat TCP-LISTEN:7777,reuseaddr,fork OPENSSL:$SERVER,cert=$CERT,verify=0,openssl-cipherlist=HIGH:@SECLEVEL=0"
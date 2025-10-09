#!/bin/bash
# Tunnel SSL simple avec socat
# Port local 7777 -> epp.gtld.knet.cn:700

echo "🚀 Démarrage tunnel SSL..."
echo "   Local:  localhost:7777"
echo "   Remote: epp.gtld.knet.cn:700"
echo "   Certs:  certs/epp.gtld.knet.cn.pem"
echo ""
echo "💡 Pour tester:"
echo "   telnet localhost 7777"
echo "   echo 'test' | nc localhost 7777"
echo "   python3 send_to_tunnel.py login"
echo "🛑 Pour arrêter: Ctrl+C"
echo ""

socat TCP-LISTEN:7777,reuseaddr,fork \
      OPENSSL:epp.gtld.knet.cn:700,cert=certs/epp.gtld.knet.cn.pem,key=certs/epp.gtld.knet.cn.pem,verify=0
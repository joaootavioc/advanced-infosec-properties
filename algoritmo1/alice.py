#!/usr/bin/env python3
import socket, hmac, hashlib, sys
from cryptography.fernet import Fernet
from comandos import * # Importa os comandos PUT, PUT_ACK, GET, GET_ACK, e NOTIFY


def main():
    nonce_cliente = 0
    sock = conectar(PORTA, ID_CLIENTE) # Conecta-se com o servidor no IP local e na PORTA escolhida
    sock.send(bytes(adicionar_padding(ID_CLIENTE), 'utf-8')) # Informa o ID do cliente
    resposta = remover_padding(sock.recv(TAM_PAYLOAD)) # Recebe a resposta do servidor
    print(resposta)
    aviso_pendentes = remover_padding(sock.recv(TAM_PAYLOAD)) # Recebe a resposta do servidor
    print(aviso_pendentes)

    # Gerencia publicação da mensagem e recebimento do ACK
    publicar_mensagem(sock, nonce_cliente, 'G1', 'Olá grupo!', CHAVE_SECRETA)

    sock.close()

    print("[+] Conexão com o servidor encerrada.")


if len(sys.argv) < 2:
    print(f"[+] Utilização: {sys.argv[0].lstrip('./')} <porta>")
    print("[+] <porta> : Porta da rede na qual o servidor vai operar")
    raise SystemExit

try:
    PORTA = int(sys.argv[1])
except ValueError:
    print("[+] Por favor utilize somente números inteiros para a porta.")
    raise SystemExit


TAM_PAYLOAD = 512
ID_CLIENTE = 'Alice'
CHAVE_SECRETA = b'WRprQNey0P5VH1JoCcMW-2PW6GZjKxIq6unPLF8QCG8='


main()

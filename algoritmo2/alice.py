#!/usr/bin/env python3
import socket, sys
from comandos import * # Importa os comandos PUT, PUT_ACK, GET, GET_ACK, e NOTIFY

''' Algoritmo 3:
    Geração e atualização de chaves secretas de sessão '''

def main():
    nonce_cliente = 0
    sock = conectar(PORTA) # Conecta-se com o servidor no IP local e na PORTA escolhida

    p, g = gerar_parametros() # Prepara os parâmetros para a troca de chaves de Diffie-Hellman
    chave_longa_duracao = solicitar_diffie_hellman(p, g, sock) # Solicita a geração de uma chave através do processo de Diffie-Hellman

    sock.send(bytes(adicionar_padding(ID_CLIENTE), 'utf-8')) # Informa o ID do cliente
    resposta = remover_padding(sock.recv(TAM_PAYLOAD)) # Recebe a resposta do servidor
    print(resposta)

    aviso_pendentes = remover_padding(sock.recv(TAM_PAYLOAD)) # Recebe informação sobre mensagens pendentes
    print(aviso_pendentes)

    chave_longa_duracao = atualizar_chave(chave_longa_duracao)

    publicar_mensagem(sock, nonce_cliente, 'G1', 'Olá grupo!', chave_longa_duracao) # Solicita publicação de uma mensagem

    sock.close() # Encerra a conexão

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
ID_CLIENTE = 'cliente1'

main()

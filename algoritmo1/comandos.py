import hmac, hashlib, socket
from cryptography.fernet import Fernet

''' Esse arquivo define algumas funções úteis para
os exemplos sobre Perfect Forward Secrecy e Post-Compromise
Security '''

TAM_PAYLOAD = 512

def criptografar(mensagem, chave):
    ''' Criptografa uma string usando uma chave e o algoritmo Fernet '''
    mecanismo = Fernet(chave)
    return mecanismo.encrypt((mensagem).encode())


def decodificar(mensagem, chave, comando):
    ''' Decodifica uma mensagem utilizando uma chave e o algoritmo Fernet '''
    mecanismo = Fernet(chave)
    mensagem = mecanismo.decrypt(mensagem.encode()).decode()
    if comando == 'PUT' or comando == 'GTA':
        grupo = mensagem[:2]
        return grupo, mensagem[2:]
    elif comando == 'PTA' or comando == 'NTF':
        return '', mensagem
    elif comando == 'GET':
        return mensagem, ''


def verificar_hmac(payload, chave):
    ''' Verifica a integridade do payload recebido atraves do codigo HMAC '''
    payload = remover_padding(payload)
    msg_hmac = payload[-64:] # Os últimos 64 caracteres do payload são o HMAC
    dados = payload[:-64]
    h = hmac.new(chave, dados.encode(), hashlib.sha256)
    if h.hexdigest() == msg_hmac:
        return 'OK'
    else:
        return 'NOK'


def gerar_hmac(chave, info):
    ''' Gera um codigo HMAC para permitir a verificacao da integridade de uma string '''
    h = hmac.new(chave, info.encode(), hashlib.sha256)
    return h.hexdigest()


def adicionar_padding(mensagem):
    ''' Preenche a mensagem com espacos vazios ate atingir o tamanho do payload '''
    encoded_size = len(bytes(mensagem.encode()))
    padding = (TAM_PAYLOAD - encoded_size + len(mensagem))
    # Preenche o final da mensagem com espaços vazios
    return mensagem.ljust(padding, ' ')


def remover_padding(mensagem):
    ''' Remove os espacos vazios ao final da mensagem, recuperando os dados originais '''
    # Remove o preenchimento ao final da mensagem
    return mensagem.decode().rstrip(' ')


def put(destino, nonce, grupo, mensagem, chave):
    ''' Envia o comando PUT, solicitando a publicacao de uma mensagem em um grupo '''
    payload = ''
    payload += "PUT" + '/' # Comando PUT
    payload += str(nonce) + '/'
    msg_criptografada = criptografar(grupo + mensagem, chave) # Criptografa os dados da mensagem usando a chave secreta
    payload += msg_criptografada.decode() + '/'
    payload += gerar_hmac(chave, payload) # Adiciona um HMAC ao payload para ajudar a verificar a integridade dos dados
    payload = adicionar_padding(payload) # Preenche o restante do espaço do payload com espaços vazios
    destino.send(bytes(payload, 'utf-8'))
    nonce += 1
    print(f"[+] Mensagem publicada: ({grupo}) {mensagem}")
    return


def put_ack(destino, nonce, chave):
    ''' Envia o comando PUT_ACK, notificando o recebimento do comando PUT '''
    payload = ''
    payload += "PTA" + '/' # Comando PUT_ACK
    payload += str(nonce) + '/'
    msg_criptografada = criptografar(f"[+] Mensagem (Nonce: {nonce}) entregue!\n", chave)
    payload += msg_criptografada.decode() + '/'
    payload += gerar_hmac(chave, payload)
    destino.send(bytes(payload, 'utf-8'))
    return


def extrair_dados(payload, chave):
    ''' Extrai os dados contidos nos diferentes campos da mensagem '''
    if verificar_hmac(payload, chave) == 'NOK': # Verifica a integridade da mensagem
        print("[+] HMAC incompatível com a mensagem recebida.")
        raise SystemExit
    payload = remover_padding(payload)
    comando, nonce, msg_criptografada, hmac = payload.split('/')
    grupo, mensagem = decodificar(msg_criptografada, chave, comando)
    return comando, int(nonce), grupo, mensagem


def get(destino, nonce, grupo, chave):
    ''' Envia o comando GET, requisitando mensagens pendentes em um grupo '''
    payload = ''
    payload += "GET" + '/' # Comando GET
    payload += str(nonce) + '/'
    msg_criptografada = criptografar(grupo, chave) # Criptografa os dados da mensagem usando a chave secreta
    payload += msg_criptografada.decode() + '/'
    payload += gerar_hmac(chave, payload)
    destino.send(bytes(payload, 'utf-8'))
    return


def get_ack(destino, nonce, mensagem, grupo, chave):
    ''' Envia o comando GET_ACK, notificando o recebimento de um comando GET '''
    payload = ''
    payload += "GTA" + '/' # Comando PUT_ACK
    payload += str(nonce) + '/'
    msg_criptografada = criptografar(grupo + mensagem, chave) # Criptografa os dados da mensagem usando a chave secreta
    payload += msg_criptografada.decode() + '/'
    payload += gerar_hmac(chave, payload)
    destino.send(bytes(payload, 'utf-8'))
    return


def notify(destino, nonce, lista_grupos, chave):
    ''' Envia o comando NOTIFY, que notifica o cliente sobre a existencia de novas mensagens '''
    payload = ''
    payload += "NTF" + '/' # Comando NOTIFY
    payload += str(nonce) + '/'
    msg_criptografada = criptografar("[+] Mensagens pendentes nos grupos: " + ','.join(lista_grupos), chave) # Criptografa os dados da mensagem usando a chave secreta
    payload += msg_criptografada.decode() + '/'
    payload += gerar_hmac(chave, payload)
    destino.send(bytes(payload, 'utf-8'))
    return

def conectar(PORTA, ID_CLIENTE):
    ''' Estabelece uma conexao com o servidor de mensagens no endereco local e na porta especificada '''
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Instancia um socket
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Impede que o socket fique ocupado após a execução
    try:
        sock.connect((socket.gethostname(), PORTA)) # Conecta com o servidor na porta 5555
        print("[+] Conexão com {} estabelecida.\n".format(sock.getsockname()))
    except ConnectionError:
        print("[+] Erro na conexão com o servidor.")
        raise SystemExit
    return sock


def publicar_mensagem(sock, nonce, grupo, mensagem, chave):
    ''' Gerencia o processo de publicacao da mensagem e recebimento da confirmacao '''
    put(sock, nonce, 'G1', 'Olá grupo!', chave) # Publica uma mensagem
    resposta = sock.recv(TAM_PAYLOAD)
    comando, nonce_recebido, grupo, mensagem = extrair_dados(resposta, chave)

    if nonce_recebido != nonce:
        print("[+] Erro na sincronia das mensagens.")

    if comando == 'PTA': # Recebeu um ACK do servidor
        nonce += 1 # Após receber a confirmação do servidor, incrementa o nonce
        print(f"{mensagem}")

    return


def recuperar_mensagem(sock, nonce, grupo, chave):
    ''' Gerencia o processo de requisicao de mensagem e recebimento dos dados '''
    get(sock, nonce, grupo, chave)
    print("[+] Solicitando mensagens... \n")
    resposta = sock.recv(TAM_PAYLOAD)
    comando, nonce_recebido, grupo, mensagem = extrair_dados(resposta, chave)

    if nonce_recebido != nonce:
        print("[+] Erro na sincronia das mensagens.")

    if comando == 'GTA': # Recebeu um GET_ACK do servidor
        nonce += 1 # Após receber a confirmação do servidor, incrementa o nonce
        print(f"[+] Mensagem recebida:\n\t{mensagem}")

    return


def tratar_cliente(socket_cliente, id_cliente, chave, payload, grupos, mensagens_pendentes, nonce_esperado):
    comando, nonce_recebido, grupo, mensagem = extrair_dados(payload, chave)

    if nonce_recebido != nonce_esperado: # Verifica se as mensagens estão na sequência correta
        print("[+] Erro na sincronia das mensagens. \n")
        return

    if comando == 'PUT': # O cliente deseja publicar uma mensagem
        print(f"[+] Requisição de publicação de mensagem recebida de: {id_cliente}\n")
        print(f"[+] Grupo: {grupo} | Mensagem: {mensagem} \n")
        if grupo in grupos: # Se o grupo existe
            if id_cliente in grupos[grupo]: # Se o cliente que enviou a mensagem está no grupo
                for cliente in grupos[grupo]:
                    if cliente != id_cliente: # Envia a mensagem para os outros clientes
                        mensagens_pendentes[cliente].append('(' + grupo + ') ' + id_cliente + ': ' + mensagem + '\n')
                        print("[+] Mensagem publicada.\n")
                        put_ack(socket_cliente, nonce_recebido, chave)
                        nonce_esperado += 1

    elif comando == 'GET': # O cliente deseja recuperar mensagens
        print(f"[+] Requisição de recuperação de mensagem recebida de: {id_cliente}\n")
        for cliente in mensagens_pendentes:
            if cliente == id_cliente:
                if cliente in mensagens_pendentes.keys() and len(mensagens_pendentes[cliente]) > 0:
                    for mensagem in mensagens_pendentes[cliente]:
                        if mensagem[1:3] == grupo: # Se a mensagem corresponde ao grupo solicitado
                            get_ack(socket_cliente, nonce_recebido, mensagem, grupo, chave)
                            print(f"[+] Mensagens pendentes enviadas para {id_cliente}\n")
                            nonce_esperado += 1
                            break
                else:
                    print("[+] Não há mensagens pendentes. \n")


def verifica_pendentes(id_cliente, mensagens_pendentes):
    lista_grupos = []
    for cliente in mensagens_pendentes:
        if cliente == id_cliente: # Verifica as mensagens do cliente em questão
            if cliente in mensagens_pendentes.keys() and len(mensagens_pendentes[cliente]) > 0: # Se há mensagens pendentes
                for mensagem in mensagens_pendentes[cliente]: # Para cada mensagem recebida
                    if mensagem[:4] not in lista_grupos: # Se ainda não há notificação sobre o grupo
                        lista_grupos.append(mensagem[:4]) # Adiciona uma notificação sobre o grupo
    return lista_grupos

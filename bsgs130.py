import subprocess
import time
import os
import signal
import pickle
import random

# Função para salvar o checkpoint
def save_checkpoint(start_keyspace, end_keyspace):
    checkpoint_data = {
        'start_keyspace': start_keyspace,
        'end_keyspace': end_keyspace
    }
    with open('checkpoint.pkl', 'wb') as f:
        pickle.dump(checkpoint_data, f)

# Função para carregar o checkpoint
def load_checkpoint():
    if os.path.exists('checkpoint.pkl'):
        with open('checkpoint.pkl', 'rb') as f:
            checkpoint_data = pickle.load(f)
        return checkpoint_data['start_keyspace'], checkpoint_data['end_keyspace']
    else:
        return '320000000000000000000000000000000', '321000000000000000000000000000000'

def delete_checkpoint():
    if os.path.exists('checkpoint.pkl'):
        os.remove('checkpoint.pkl')

def run_keyhunt(start_keyspace, end_keyspace):
    command = f'./keyhunt -m bsgs -f tests/130.txt -k 768 -t 96 -s 10 -R -S -M -r {start_keyspace}:{end_keyspace}'
    
    # Executa o comando no Colab
    process = subprocess.Popen(command, shell=True, preexec_fn=os.setsid)
    time.sleep(600)  # Espera 10 minutos
    os.killpg(os.getpgid(process.pid), signal.SIGTERM)  # Envia sinal para terminar o processo
    process.wait()  # Espera o processo terminar

# Carrega o checkpoint se existir, caso contrário, começa do início
start_keyspace, end_keyspace = load_checkpoint()

# Loop até ser explicitamente interrompido
last_save_time = time.time()  # Rastreia o último tempo de salvamento
save_interval = 600  # Intervalo de salvamento em segundos (10 minutos)

while True:
    try:
        # Gera um incremento randômico entre 1e28 e 1e32
        random_increment = random.randint(0x1000000000000000000000000000, 0x100000000000000000000000000000)
        increment = hex(random_increment)[2:]

        while int(end_keyspace, 16) <= int('32fffffffffffffffffffffffffffffff', 16):  # Continua até atingir o valor final do keyspace
            run_keyhunt(start_keyspace, end_keyspace)
            start_keyspace = hex(int(end_keyspace, 16) + 1)[2:]  # Incrementa o valor do keyspace inicial
            end_keyspace = hex(int(start_keyspace, 16) + random_increment - 1)[2:]  # Incrementa o valor do keyspace final corretamente

            # Salva o checkpoint a cada 10 minutos
            current_time = time.time()
            elapsed_time = current_time - last_save_time
            if elapsed_time >= save_interval:
                save_checkpoint(start_keyspace, end_keyspace)
                last_save_time = current_time

            time.sleep(3)  # Espera 3 segundos antes de reiniciar

        # Deleta o arquivo de checkpoint quando o start_keyspace começa com '36xxxxxxx'
        if start_keyspace.startswith('36'):
            delete_checkpoint()
            start_keyspace, end_keyspace = load_checkpoint()
        else:
            break
        
    except KeyboardInterrupt:
        save_checkpoint(start_keyspace, end_keyspace)  # Salva o checkpoint se interrompido por KeyboardInterrupt
        break

# Deleta o arquivo de checkpoint no final do keyspace
delete_checkpoint()

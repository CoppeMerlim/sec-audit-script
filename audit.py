import subprocess
import requests

# Configurações do Alvo
# Importante: O 'ab' exige a barra '/' no final se for apenas o domínio
TARGET_URL = "https://cloud.plataforma.senac.br/"
TARGET_DOMAIN = "cloud.plataforma.senac.br"

def run_command(command):
    try:
        #  shell=True para facilitar o uso de pipes (|) se necessário
        result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        return result.decode('utf-8', errors='ignore')
    except subprocess.CalledProcessError as e:
        return f"Erro ao executar comando: {e.output.decode('utf-8', errors='ignore')}"

def check_dns():
    print(f"\n--- 1. ANALISANDO DNS ({TARGET_DOMAIN}) ---")
    dns_info = run_command(f"nslookup {TARGET_DOMAIN}")
    print(dns_info)

def check_security_headers():
    print("\n--- 2. VERIFICANDO HEADERS DE SEGURANÇA ---")
    try:
        response = requests.get(TARGET_URL, timeout=10)
        headers = response.headers
        for header in ["Strict-Transport-Security", "X-Content-Type-Options", "Content-Security-Policy"]:
            print(f"[>] {header}: {headers.get(header, 'Ausente')}")
    except Exception as e:
        print(f"Erro na conexão: {e}")

def check_waf():
    print("\n--- 3. TESTE DE CAMADA 7 (WAF) ---")
    payload = "<script>alert('test')</script>"
    try:
        # Tenta injetar um script simples via query string
        res = requests.get(f"{TARGET_URL}?id={payload}", timeout=10)
        if res.status_code == 403:
            print("Resultado: [BLOQUEADO] WAF ativo detectado (403 Forbidden).")
        else:
            print(f"Resultado: [ALERTA] Requisição aceita ({res.status_code}). Possível ausência de WAF.")
    except Exception as e:
        print(f"Erro no teste de WAF: {e}")

def run_stress_test(concurrency, requests_count):
    print(f"\n--- 4. STRESS TEST: {concurrency} USUÁRIOS SIMULTÂNEOS ---")
    # Executa o Apache Benchmark
    cmd = f"ab -n {requests_count} -c {concurrency} {TARGET_URL}"
    output = run_command(cmd)
    
    if "Erro" in output:
        print("Certifique-se de que o 'ab' (apache2-utils) está instalado.")
        return

    metrics = {
        "Requests per second:": "Vazão (Throughput)",
        "Time per request:": "Latência Média",
        "Failed requests:": "Requisições Falhas",
        "Non-2xx responses:": "Erros de Servidor (5xx/4xx)"
    }
    
    for line in output.split('\n'):
        for key, label in metrics.items():
            if key in line:
                # Se for o 'Time per request' que contém '(mean)', pegamos apenas ele
                if key == "Time per request:" and "(mean)" not in line:
                    continue
                print(f"    {label}: {line.split(':')[1].strip()}")

if __name__ == "__main__":
    print(f"=== INICIANDO AUDITORIA: {TARGET_DOMAIN} ===")
    
    check_dns()
    check_security_headers()
    check_waf()
    
    # Teste comparativo 
    # Cenário A: Carga Leve
    run_stress_test(concurrency=10, requests_count=100)
    
    # Cenário B: Carga Moderada (Aumenta a chance de ver gargalos)
    run_stress_test(concurrency=50, requests_count=200)
    
    print("\n=== AUDITORIA FINALIZADA ===")

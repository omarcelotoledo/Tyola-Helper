"""
Tyola PC — deixa a Tyola abrir sites, programas e digitar no seu computador.

Como usar:
  1. Instale o Python 3 (python.org). No Windows, marque "Add Python to PATH".
  2. (Opcional, pra Tyola DIGITAR em qualquer janela)  pip install pyautogui
  3. Rode:  python tyola_pc.py
     e digite o código que aparece na Tyola (menu › Conectar ao PC). Ex.: K3M9-X2Q7
  4. Deixe esta janela aberta. Pra parar: Ctrl+C.

Segurança: a Tyola só consegue fazer o que está na lista abaixo (abrir sites, pesquisar,
abrir alguns programas e digitar texto). Ela NUNCA roda comandos livres no seu computador.
Não compartilhe o código: quem souber o código consegue mandar esses comandos.
"""
import json
import platform
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
import webbrowser

NTFY = "https://ntfy.sh"
SISTEMA = platform.system()  # "Windows", "Darwin" (Mac) ou "Linux"

# Programas que a Tyola pode abrir (só estes!). Ajuste o caminho do Minecraft se precisar.
PROGRAMAS = {
    "Windows": {
        "calculator": ["calc.exe"],
        "notepad":    ["notepad.exe"],
        "paint":      ["mspaint.exe"],
        "explorer":   ["explorer.exe"],
        "settings":   ["cmd", "/c", "start", "", "ms-settings:"],
        "minecraft":  ["cmd", "/c", "start", "", "minecraft:"],   # Minecraft Launcher da Microsoft Store
    },
    "Darwin": {
        "calculator": ["open", "-a", "Calculator"],
        "notepad":    ["open", "-a", "TextEdit"],
        "paint":      ["open", "-a", "Preview"],
        "explorer":   ["open", "-a", "Finder"],
        "settings":   ["open", "-a", "System Settings"],
        "minecraft":  ["open", "-a", "Minecraft"],
    },
    "Linux": {
        "calculator": ["gnome-calculator"],
        "notepad":    ["gedit"],
        "paint":      ["pinta"],
        "explorer":   ["xdg-open", "."],
        "settings":   ["gnome-control-center"],
        "minecraft":  ["minecraft-launcher"],
    },
}

try:
    import pyautogui  # opcional
except Exception:
    pyautogui = None


def enviar(topico, dados):
    """Manda um recado de volta pra Tyola (ela mostra na legenda)."""
    corpo = json.dumps({"from": "pc", **dados}).encode("utf-8")
    try:
        urllib.request.urlopen(urllib.request.Request(f"{NTFY}/{topico}", data=corpo, method="POST"), timeout=10)
    except Exception as e:
        print("  (não consegui responder pra Tyola:", e, ")")


def abrir_site(url):
    if not url.startswith(("http://", "https://")):
        return "Endereço inválido"
    webbrowser.open(url)
    return "Abri o site no PC"


def abrir_programa(nome):
    cmd = PROGRAMAS.get(SISTEMA, {}).get(nome)
    if not cmd:
        return f"Não sei abrir {nome} neste computador"
    try:
        subprocess.Popen(cmd)
        return f"Abri {nome} no PC"
    except Exception as e:
        print("  erro ao abrir:", e)
        return f"Não consegui abrir {nome}"


def digitar(texto):
    if pyautogui is None:
        print("  [Tyola quer digitar]:", texto)
        print("  (instale com:  pip install pyautogui  pra ela digitar na janela que estiver aberta)")
        return "Mostrei o texto na janela do Tyola PC"
    time.sleep(0.6)
    pyautogui.write(texto, interval=0.02)
    return "Digitei no PC"


def executar(topico, m):
    if m.get("from") != "tyola":
        return
    tipo = m.get("type")
    if tipo == "ping":
        enviar(topico, {"type": "hello"})
        return
    if tipo != "cmd":
        return
    cmd = m.get("cmd")
    print(f"→ Tyola pediu: {cmd}  {m.get('url') or m.get('q') or m.get('text') or m.get('name') or ''}")
    if cmd == "open":
        info = abrir_site(str(m.get("url", "")))
    elif cmd == "search":
        q = str(m.get("q", ""))[:200]
        info = abrir_site("https://www.google.com/search?q=" + urllib.parse.quote(q))
    elif cmd == "app":
        info = abrir_programa(str(m.get("name", "")))
    elif cmd == "type":
        info = digitar(str(m.get("text", ""))[:2000])
    else:
        info = "Comando desconhecido"
    enviar(topico, {"type": "ack", "info": info})


def batimento(topico):
    """Avisa a Tyola a cada 30 s que o PC está ligado."""
    while True:
        enviar(topico, {"type": "hello"})
        time.sleep(30)


def ouvir(topico):
    url = f"{NTFY}/{topico}/json"
    while True:
        try:
            with urllib.request.urlopen(url, timeout=90) as resp:
                print("✓ Conectado. Esperando pedidos da Tyola…  (Ctrl+C pra sair)")
                for linha in resp:
                    try:
                        d = json.loads(linha.decode("utf-8"))
                    except ValueError:
                        continue
                    if d.get("event") != "message":
                        continue
                    try:
                        executar(topico, json.loads(d.get("message", "")))
                    except ValueError:
                        pass
        except KeyboardInterrupt:
            raise
        except Exception as e:
            print("  conexão caiu (", e, "), tentando de novo em 3 s…")
            time.sleep(3)


def main():
    codigo = sys.argv[1] if len(sys.argv) > 1 else input("Código da Tyola (ex.: K3M9-X2Q7): ")
    limpo = "".join(ch for ch in codigo.upper() if ch.isalnum())
    if len(limpo) != 8:
        print("O código tem 8 letras/números. Confira no menu da Tyola.")
        return
    topico = "tyola-" + limpo.lower()
    print(f"Tyola PC ({SISTEMA}) — código {limpo[:4]}-{limpo[4:]}")
    if pyautogui is None:
        print("Dica: pip install pyautogui  → a Tyola consegue digitar em qualquer janela.")
    threading.Thread(target=batimento, args=(topico,), daemon=True).start()
    try:
        ouvir(topico)
    except KeyboardInterrupt:
        print("\nTchau! A Tyola desconectou deste PC.")


if __name__ == "__main__":
    main()

#
#
#
#            WOL AGENT 0.1 - script python 3
#            Écrit par Antoine Jové le 15/07/2026
#            Avec l'assistance de Chat GPT 4
#            -----------------------------------------------
#            Le script récupère les données d'une API
#            Supabase définie dans le fichier config.py
#            Puis crée un Payload basée sur l'adresse MAC
#            du PC a réveiller avant d'effectuer une requête
#            Wake-On-LAN
#            -----------------------------------------------
#
#
# Importation des bibliothèques
import time
import socket
import requests
# On récupère les éléments de config du fichier ./config.py
from config import (
    SUPABASE_URL,
    SERVICE_ROLE_KEY,
    POLL_INTERVAL,
    WOL_PORT,
    WOL_BROADCAST
)

# On crée l'en-tête d'authetification de l'appel à l'API de Supabase
HEADERS = {
    "apikey": SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
    "Content-Type": "application/json"
}

# Fonction de création du payload du magic paquet utilisé pour le Wake On LAN
def send_magic_packet(mac):
    """
    Envoie un Magic Packet Wake-on-LAN
    """

    mac = mac.replace(":", "").replace("-", "")

    if len(mac) != 12:
        raise ValueError("Adresse MAC invalide")

    data = bytes.fromhex("FF" * 6 + mac * 16)

    sock = socket.socket(
        socket.AF_INET,
        socket.SOCK_DGRAM
    )

        sock.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_BROADCAST,
        1
    )

    sock.sendto(
        data,
        (WOL_BROADCAST, WOL_PORT)
    )

    sock.close()

# Fonction de requête vers l'API de Supabase
def get_pending_requests():

    url = (
        f"{SUPABASE_URL}/rest/v1/"
        "wol_requests"
        "?status=eq.pending"
    )

    r = requests.get(
        url,
        headers=HEADERS
    )

    r.raise_for_status()

    return r.json()

# Fonction qui vérifie si une machine doit être réveillée
def get_machine(machine_id):

    url = (
        f"{SUPABASE_URL}/rest/v1/"
        "machines"
        f"?id=eq.{machine_id}"
    )

    r = requests.get(
        url,
        headers=HEADERS
    )

        r.raise_for_status()

    machines = r.json()

    if not machines:
        return None

    return machines[0]

# Fonction de mise à jour de l'état de la requête WOL dans Supabase
def update_request(request_id, status):

    url = (
        f"{SUPABASE_URL}/rest/v1/"
        "wol_requests"
        f"?id=eq.{request_id}"
    )

    r = requests.patch(
        url,
        headers=HEADERS,
        json={
            "status": status
        }
    )

    r.raise_for_status()

# Fonction de vérification des machines à démarrer
def process_requests():

    requests_list = get_pending_requests()

    for req in requests_list:

        request_id = req["id"]
        machine_id = req["machine_id"]

        print(
            f"Traitement demande {request_id}"
        )

                try:

            machine = get_machine(machine_id)

            if not machine:
                raise Exception(
                    "Machine inconnue"
                )

            mac = machine["mac"]

            print(
                f"Wake {machine['name']} {mac}"
            )

            send_magic_packet(mac)

            update_request(
                request_id,
                "done"
            )

        except Exception as e:

            print(
                "Erreur:",
                e
            )

            update_request(
                request_id,
                "failed"
            )

# Fonction principale
def main():

    print("WOL Agent démarré")

    while True:
        try:
            process_requests()

        except Exception as e:
            print(
                "Erreur générale:",
                e
            )

        time.sleep(
            POLL_INTERVAL
        )


if __name__ == "__main__":
    main()

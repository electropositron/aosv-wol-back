# Description du projet
Ce dépôt héberge un script python 3 à exécuter comme un daemon qui permet d'aller chercher des requêtes de Wake On Lan stockée sur une base de données Progresql hébergée chez Supabase via son API puis d'envoyer des magic paquets sur le réseau local à destination des machines dont les adresses MAC sont contenues dans les entrées de chaque requête.
## Dépendances
Ce script utilise les dépendances suivantes :
- os
- time
- socket
- requests
## Variables
Ce script a besoin de variables définies par l'utilisateur pour pouvoir fonctionner :
SUPABASE_URL : l'URL de la base de données Supabase
SERVICE_ROLE_KEY : la clef privée de la table Supabase
POLL_INTERVAL : la fréquence des requêtes vers la base de donnée pour voir si de nouvelles requêtes WOL ont été écrites par l'utilisateur
WOL_PORT : le port UDP sur lequel les magic packets doivent être émis
WOL_BROADCAST : l'adresse de boradcast du réseau sur lequel émettre les magic paquets
## Exécution
Le script est exécuté avec la commande suivante :
```
nohup python3 wol_agent.py > wol_agent.log 2>&1 &
```
Il s'exécute en arrière plan même si la session depuis laquelle il a été lancé est éteinte. Il écrit la sortie standard et la sortie d'erreurs dans un fichier wol_agent.log situé dans le répertoire d'exécution du programme. Et comme une entrée a été ajoutée dans une entrée init/startup task, il est relancé automatiquement à chaque redémarrage de la machine.
Pour vérifier si le programme s'éxécute toujours, ouvrir le terminal de la machine locale et exécuter
```
ps aux | grep '[w]ol_agent'
```
## Fonctions principales
### Envoi d'un magic paquet
```
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
```
### Fonctions qui vérifient les entrées en sttaut 'pending' sur Supa base puis qui vérifie à quelle machine elle correspond
```
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
```

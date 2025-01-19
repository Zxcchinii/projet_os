VM 500 -> Linux avec GUI (client)
VM 501 -> Linux sans GUI (server)

Projet Puissance 4 :

sur le client (VM 500), ouvrir Firefox et entrer l'URL suivante : http://localhost:8081
Vous devez vous retrouver devant un écran de choix. 

Si ce n'est pas le cas, aller sur le serveur (VM 501) et rentrer la commande suivante dans le dossier projet : docker-compose up --build -d
et aller sur le client (VM 500) dans le dossier projet et rentrer la même commande.

Description des choix : 

Jouer avec le serveur fait que le serveur choisira une position aléatoire pour le jeton

Jouer avec un autre joueur :

Comme wsl ne marche pas sur Windows, j'aurais dû créer une nouvelle vm donc la fonctionnalité ne fonctionne pas

P.S - Le mot de passe pour la VM 500 / 501 est ensibs. Par contre, le mot de passe pour la connection à distance proxmox est ENSIBS avec root comme username 

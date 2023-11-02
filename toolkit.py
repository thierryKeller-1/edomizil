import argparse
from datetime import datetime, timedelta


def main_arguments() -> object:
    parser = argparse.ArgumentParser(description="Edomizil program",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--action', '-a', dest='action', default='',
                        help="""Tâche à faire: \n \t 'init': actualiser la liste des destinations. | 'start': Lancer le scraping des annonces. | 'clean': pour nettoyer le résultat""")
    parser.add_argument('--stations', '-s', dest='stations', default='', help="Nom du station a scraper")
    parser.add_argument('--name', '-n', dest='name',
                        default='', help="Nom du fichier qui va contenir les donner")
    parser.add_argument('--start-date', '-b', dest='start_date',
                        default='', help="Date début format 'dd/mm/YYYY'")
    parser.add_argument('--end-date', '-e', dest='end_date',
                        default='', help="Date fin format 'dd/mm/YYYY'")
    parser.add_argument('--destination', '-d', dest='destination', default='', help="Nom du fichier contenant la liste des destinations")
    parser.add_argument('--principal-program','-fp', dest='principal', default=None, help="Seul le programme principale peut changer l'adresse IP.")
    parser.add_argument('--import-tag','-it', dest='tag', default='', help="Tag des accommodations à supprimer")
    return parser.parse_args()


ARGS_INFO = {
        '-a': {'long': '--action', 'dest': 'action', 'help': """Tâche à faire: \n \t
        'init': Récupération des urls à scraper. | 'start': Lancer le scraping des annonces. | 'clean': Nettoyer le résultat"""},
        '-d': {'long': '--destination', 'dest': 'destination', "help": "chemin du fichier contenant les destinations"},
        '-n': {'long': '--name', 'dest': 'name', "help": "Nom du fichier qui va contenir les donner"},
        '-st': {'long': '--storage', 'dest': 'storage', "help": "Chemin de stockage du fichier contenant les resultats"},
        '-b': {'long': '--start-date', 'dest': 'start_date', "help": "Date début format 'dd/mm/YYYY'"},
        '-e': {'long': '--end-date', 'dest': 'end_date', "help": "Date fin format 'dd/mm/YYYY'"},
        '-s': {'long': '--stations', 'dest': 'stations', "help": "Nom du fichier contenant la liste des stations ou regions"},
        '-fp': {'long': '--principal-program', 'dest': 'principal', 'help': "Seul le programme principale peut changer l'adresse IP."}
    }

def check_arguments(args, required):
    miss = []

    for item in required:
        if not getattr(args, ARGS_INFO[item]['dest']):
            miss.append(
                f'{item} ou {ARGS_INFO[item]["long"]} ({ARGS_INFO[item]["help"]})')
    return miss
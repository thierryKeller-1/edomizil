# edomizil
emodizil scraper takes 4 arguments:
    filename = "string that will be take as the name of log file and the resulta csv file"
    dest = "the name of the file that contains the list of destination links
    date_start = " the monday of week when scrap is launched "
    date_end = " the last day of month when scrap will be stoped"

STATIC_FOLDER_PATH="/home/dev/work/www/suisse/edomizil/static"
LOG_FOLDER_PATH="/home/dev/work/www/suisse/edomizil/logs"
CONFIG_FOLDER_PATH="/home/dev/work/www/suisse/edomizil/configs"
OUTPUT_FOLDER_PATH="/home/dev/work/www/suisse/edomizil/results"
DESTS_FOLDER_PATH="/home/dev/work/www/suisse/edomizil/dests"

sudo nmcli con status down fr.protonvpn.net.udp
sudo nmcli con status up fr.protonvpn.net.udp




git clone https://github.com/thierryKeller-1/edomizil.git

git checkout develop

git pull origin develop

pip install virtualenv

virtualenv venv

source venv/bin/activate

pip install -r edomizil/requirements.txt

playwright install

python3 edmizil -a start -d dests.json -n results -b 25/11/2023 -e 25/05/2024
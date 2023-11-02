from dotenv import load_dotenv
from toolkit import check_arguments, main_arguments
from scraper import EdomizilScraper
from initializer import EdomizilInitScraper
import os

if __name__=='__main__':

    load_dotenv()

    args = main_arguments()

    if args.action:
        match args.action:
            case 'start':
                miss_args = check_arguments(args, ['-n', '-d', '-b', '-e'])
                if not len(miss_args):
                    e = EdomizilScraper(
                        filename=args.name,
                        dest_name=args.destination,
                        date_start=args.start_date,
                        date_end=args.end_date
                    )
                    e.start()
                else:
                    raise Exception(f"Argument(s) manquant(s): {', '.join(miss_args)}") 

            case 'init':
                miss_args = check_arguments(args, ['-n'])
                if not len(miss_args):
                    e = EdomizilInitScraper(filename=args.name)
                    e.initialize()
                else:
                    raise Exception(f"Argument(s) manquant(s): {', '.join(miss_args)}") 
    else:
        print('   => action argument should be defined in order to launch scrap')
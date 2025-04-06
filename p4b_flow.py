from prefect import flow
from parser import Parse4Brewers


# Это наш деплой, полностью повторяет main парсера
@flow
def start_point():
    parsers = [Parse4Brewers('Владимир'), Parse4Brewers('Белгород'), Parse4Brewers('Москва')]
    for parser in parsers: parser.run_parser()


# В целом, каждые 2 часа - даже более чем достаточно
if __name__ == '__main__':
    start_point.serve(name='4brewers_parser', cron='0 */2 * * *')

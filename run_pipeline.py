from extract import extract
from transform import transform


def run():
    print('Starting extraction...')
    extract()
    print('Starting transformation...')
    transform()
    print('Pipeline complete.')


if __name__ == '__main__':
    run()

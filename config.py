import configparser

def construct_dsn(config_part: configparser.SectionProxy) -> str:
    """Reusable multiple database sub-config loading"""
    app_user = config_part.get('USER')
    app_password = config_part.get('PASSWORD')
    app_host = config_part.get('HOST')
    port = config_part.get("PORT") or None
    port_db = f':{port}' if port else ''
    app_db = config_part.get('DATABASE_NAME')
    app_driver = config_part.get('DRIVER')
    app_dsn = f'{app_driver}://{app_user}:{app_password}@{app_host}{port_db}/{app_db}'

    return app_dsn


def load_config(ini_path: str):
    """loads config data from file, pointed with path"""
    config_maker = configparser.ConfigParser()
    config_maker.read(ini_path)

    return config_maker


def get_bot_token(ini_path: str  = 'config.ini') -> str:
    config = load_config(ini_path)
    tg_token = config['tg_api']

    return tg_token.get('TOKEN')


def get_database_url(ini_path: str = 'config.ini') -> str:
    config = load_config(ini_path)
    db_read = config['app_database']

    return construct_dsn(db_read)
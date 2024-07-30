class Config(object):
    TESTING=False
    DEBUG=False

class Development(Config):
    DEBUG=True

class Testing(Config):
    TESTING=True

config = {
    'development': Development,
    'testing': Testing
}
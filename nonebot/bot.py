from os import path
import nonebot


try:
    import config
except:
    import nonebot.default_config as config

if __name__ == '__main__':
    nonebot.init(config)
    nonebot.load_plugins(
        path.join(path.dirname(__file__), 'plugins'),
        'plugins'
    )
    bot = nonebot.get_bot()
    bot.run()

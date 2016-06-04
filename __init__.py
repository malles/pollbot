import time, re, logging, plugins


class PoolBots:
    def __init__(self):
        self.poolbots = {}

    def load_pools(self, bot):
        if bot.memory.exists(["poolsbot.pools"]):
            pools = bot.memory.get("poolsbot.pools")
            for poolbot_data in pools:
                self.poolbots[poolbot_data["conv_id"]] = PoolBot(poolbot_data, bot)

    def get(self, bot, conv_id):
        if conv_id not in self.poolbots:
            poolbot_data = {'conv_id': conv_id}
            self.poolbots[conv_id] = PoolBot(poolbot_data, bot)

        return self.poolbots[conv_id]

    def save(self, bot):
        poolbots_data = []
        for conv_id, _poolbot in self.poolbots.items():
            poolbots_data.append({
                'conv_id': _poolbot.conv_id
            })
        bot.memory.set_by_path(["poolsbot.pools"], poolbots_data)

    @staticmethod
    def one2one(bot, user_id, message):
        logger.info("{} unavailable for {}".format(message, user_id))
        target_conv = yield from bot.get_1to1(user_id)
        if not target_conv:
            logger.error("1-to-1 unavailable for {}".format(user_id))
            return False

        yield from bot.coro_send_message(target_conv, message)

    @staticmethod
    def user_in_converation(bot, conv_id, user):
        logger.info(" conv_id: {}".format(conv_id))
        if bot.memory.exists(["convmem", conv_id, "participants"]):
            return user.id_.chat_id in bot.memory.get_by_path(["convmem", conv_id, "participants"])

        return False

    @staticmethod
    def is_int(value):
        try:
            int(value)
            return True
        except ValueError:
            return False


class PoolBot:
    def __init__(self, poolbot_data, bot):
        self.bot = bot
        self.conv_id = poolbot_data["conv_id"]
        # pools from conv memory
        self.bot.initialise_memory(self.conv_id, "pools")
        self.bot.initialise_memory(self.conv_id, "pools_score")
        self.pools = []
        if self.bot.memory.exists(["pools", self.conv_id]):
            pools_data = bot.memory.get_by_path(["pools", self.conv_id])
            for pool_data in pools_data:
                self.create(pool_data)
        self.score = {}
        if self.bot.memory.exists(["pools_score", self.conv_id]):
            self.score = bot.memory.get_by_path(["pools_score", self.conv_id])

    def create(self, pool_data):
        self.pools.append(Pool(pool_data))

    def get(self, pool_id):
        try:
            return self.pools[(pool_id - 1)]
        except IndexError:
            return False

    def remove(self, pool_id):
        try:
            del self.pools[(pool_id - 1)]
            return True
        except IndexError:
            return False

    def count_score(self, _pool):
        if not _pool.final:
            for user_id, _bet in _pool.bets.items():
                score = 1 if _bet["name"] in _pool.winners else 0
                if _bet["name"] not in self.score:
                    self.score[_bet["name"]] = score
                else:
                    self.score[_bet["name"]] += score
            _pool.final = True

    def reset_scores(self):
        for name, score in self.score.items():
            self.score[name] = 0

    def clear_scores(self):
        self.score = {}

    def print_score(self):
        html = "<b>Current scores:</b> <br />"
        for name, score in self.score.items():
            html += "{}: <b>{}</b><br />".format(name, score)
        return html

    def print(self):
        html = "<b>Current pools:</b> <br />"
        pool_id = 1
        for _pool in self.pools:
            html += "pool {}: <b>{}</b><br />".format(pool_id, _pool.name, _pool.descr)
            if _pool.descr:
                html += "{}<br />".format(_pool.descr)
            if not _pool.open:
                html += " <b>(closed)</b>"
            if _pool.secret:
                html += " <b>(secret)</b>"
            html += "<br />"
            pool_id += 1
        return html

    def save(self, bot):
        pools_data = []
        for _pool in self.pools:
            pools_data.append({
                'name': _pool.name,
                'descr': _pool.descr,
                'answer': _pool.answer,
                'final': _pool.final,
                'open': _pool.open,
                'secret': _pool.secret,
                'winners': _pool.winners,
                'bets': _pool.bets,
            })
        bot.memory.set_by_path(["pools", self.conv_id], pools_data)


class Pool:
    def __init__(self, pool_data):
        self.name = pool_data["name"]
        self.descr = pool_data["descr"]
        self.answer = pool_data["answer"]
        self.open = pool_data["open"]
        self.final = pool_data["final"]
        self.secret = pool_data["secret"]
        self.winners = pool_data["winners"]
        self.bets = pool_data["bets"]

    def set_descr(self, value):
        self.descr = value

    def set_open(self, value):
        self.open = value

    def set_secret(self, value):
        self.secret = value

    def set_answer(self, value):
        self.answer = value
        for user_id, _bet in self.bets.items():
            if _bet["value"] == value:
                self.winners.append(_bet["name"])

    def set_winner(self, value):
        for user_id, _bet in self.bets.items():
            logger.info("Winners: {} - {}".format(value, _bet["name"]))
            if re.search(re.escape(value), _bet["name"]):
                self.winners.append(_bet["name"])

    def set_bet(self, user, value):
        self.bets[user.id_.chat_id] = {
            'time': time.time(),
            'name': user.full_name,
            'value': value
        }

    def print(self, is_admin=False):
        html = "<b>{}</b> <br />".format(self.name)
        if self.descr:
            html += "<i>{}</i> <br />".format(self.descr)
        if not self.open:
            html += "<b>**closed**</b><br />"
        if not self.secret or is_admin:
            html += "<b>Current bets:</b> <br />"
            for user_id, _bet in self.bets.items():
                html += "{}: <b>{}</b><br />".format(_bet["name"], _bet["value"])
        else:
            html += "<i>Bets are hidden</i> <br />"

        return html

_poolbots = PoolBots()

logger = logging.getLogger(__name__)


def pool(bot, event, pool_id=None, cmd=None, *args):
    html = ""
    extern_conv = False
    _poolbot = _poolbots.get(bot, event.conv_id)

    if pool_id == 'scores':
        html = _poolbots.get(bot, event.conv_id).print_score()
    elif pool_id == 'help':
        html = "<i>View the pools:</i><br/>/bot pool<br/>"
        html += "<i>View the scores:</i><br/>/bot pool scores<br/>"
        html += "<i>View current bets of pool:</i><br/>/bot pool <id><br/>"
        html += "<i>Place a bet for pool:</i><br/>/bot pool <id> bet (<value>)<br/>"
        html += "<i>This help:</i><br/>/bot pool help<br/>"
        html += "<i>More help:</i><br/>" \
                "<a href='https://github.com/malles/poolbot'>https://github.com/malles/poolbot</a><br/>"
    elif pool_id:
        try:
            pool_id.index("||")
            conv_id = pool_id[:pool_id.index("||")].strip()
            logger.info("Voting secretly for conv_id: {}".format(conv_id))
            pool_id = int(pool_id[pool_id.index("||") + 2:])
            if not _poolbots.user_in_converation(bot, conv_id, event.user):
                yield from bot.coro_send_message(event.conv_id, "You are not in that conversation!")
                return

            extern_conv = True
            _poolbot = _poolbots.get(bot, conv_id)

        except ValueError:
            if _poolbots.is_int(pool_id):
                pool_id = int(pool_id)
            else:
                yield from bot.coro_send_message(event.conv_id, "Unknown command {}".format(pool_id))
                return

        _pool = _poolbot.get(pool_id)
        if not _pool:
            yield from bot.coro_send_message(event.conv_id, "Pool {} not found in conversation".format(pool_id))
            return

        if cmd == 'bet':
            if not _pool.open:
                html = "<b>This pool is closed for betting</b><br/>"
            elif _pool.secret and not extern_conv:
                global_pool = "{}||{}".format(event.conv_id, pool_id)
                message = "Type <i>/bot pool {} bet <value></i> in this chat to place your bet.".format(global_pool)
                yield from _poolbots.one2one(bot, event.user.id_.chat_id, message)
            else:
                _pool.set_bet(event.user, " ".join(args))
                if extern_conv or not _pool.secret:
                    html += "<b>Your bet has been set:</b><br/> {}<br/>".format(" ".join(args))
                    html += _pool.print()

        else:
            html = _pool.print()
            if _pool.open:
                html += "<br/>Type <i>/bot pool {} bet</i> to bet.<br/>"\
                    .format(pool_id, '' if _pool.secret else ' <your value>')
    else:
        html = _poolbot.print()
        html += "<br/>Type <i>/bot pool <nr> bet <your value></i> to bet.<br/>".format(pool_id)

    _poolbot.save(bot)
    _poolbots.save(bot)
    bot.memory.save()
    yield from bot.coro_send_message(event.conv_id, html)


def poolbot(bot, event, pool_id=None, cmd=None, *args):
    html = ""
    extern_conv = False
    _poolbot = _poolbots.get(bot, event.conv_id)

    if pool_id == 'reset_scores':
        _poolbot.reset_scores()
        html = _poolbots.get(bot, event.conv_id).print_score()
    if pool_id == 'clear_scores':
        _poolbot.clear_scores()
        html = _poolbots.get(bot, event.conv_id).print_score()
    elif pool_id == 'create':
        name = cmd
        _poolbot.create({
            'name': name,
            'descr': " ".join(args),
            'answer': False,
            'open': True,
            'final': False,
            'secret': False,
            'winners': [],
            'bets': {}
        })
        html = _poolbot.print()
        _poolbot.save(bot)
    elif pool_id == 'help':
        html = "<i>Create a pool:</i><br/>/bot poolbot create <name> <descr><br/>"
        html += "<i>Set description:</i><br/>/bot poolbot <id> descr <description><br/>"
        html += "<i>Set to secret:</i><br/>/bot poolbot <id> secret<br/>"
        html += "<i>Set to public:</i><br/>/bot poolbot <id> public<br/>"
        html += "<i>Close pool:</i><br/>/bot poolbot <id> close<br/>"
        html += "<i>Re-open pool:</i><br/>/bot poolbot <id> open<br/>"
        html += "<i>Remove pool:</i><br/>/bot poolbot <id> remove<br/>"
        html += "<i>Set answer:</i><br/>/bot poolbot <id> answer <answer><br/>"
        html += "<i>Set winner manually:</i><br/>/bot poolbot <id> winner <winnerslist><br/>"
        html += "<i>Announce winner:</i><br/>/bot poolbot <id> announce<br/>"
        html += "<i>This help:</i><br/>/bot pool help<br/>"
        html += "<i>More help:</i><br/>" \
                "<a href='https://github.com/malles/poolbot'>https://github.com/malles/poolbot</a><br/>"
    elif pool_id:
        try:
            pool_id.index("||")
            conv_id = pool_id[:pool_id.index("||")].strip()
            logger.info("Voting secretly for conv_id: {}".format(conv_id))
            pool_id = int(pool_id[pool_id.index("||") + 2:])
            if not _poolbots.user_in_converation(bot, conv_id, event.user):
                yield from bot.coro_send_message(event.conv_id, "You are not in that conversation!")
                return

            extern_conv = True
            _poolbot = _poolbots.get(bot, conv_id)

        except ValueError:

            if _poolbots.is_int(pool_id):
                pool_id = int(pool_id)
            else:
                yield from bot.coro_send_message(event.conv_id, "Unknown command {}".format(pool_id))
                return

        _pool = _poolbot.get(pool_id)
        if not _pool:
            yield from bot.coro_send_message(event.conv_id, "Pool {} not found in conversation".format(pool_id))
            return

        if cmd == 'descr':
            _pool.set_descr(" ".join(args))
        elif cmd == 'open':
            _pool.set_open(True)
        elif cmd == 'close':
            _pool.set_open(False)
        elif cmd == 'secret':
            _pool.set_secret(True)
        elif cmd == 'public':
            _pool.set_secret(False)
        elif cmd == 'winner':
            if not extern_conv and not len(args):
                global_pool = "{}||{}".format(event.conv_id, pool_id)
                message = "Type <i>/bot poolbot {} winner <value></i> in this chat to set winner.".format(global_pool)
            else:
                _pool.set_winner(" ".join(args))
                if len(_pool.winners) == 0:
                    message = "No winner could be picked in Pool {}<br/>".format(_pool.name)
                else:
                    message = "Winners set for Pool {}: {}<br/>".format(_pool.name, ", ".join(_pool.winners))

            message += _pool.print(True)
            yield from _poolbots.one2one(bot, event.user.id_.chat_id, message)

        elif cmd == 'answer':
            if not extern_conv and not len(args):
                global_pool = "{}||{}".format(event.conv_id, pool_id)
                message = "Type <i>/bot poolbot {} answer <value></i> in this chat to set answer.<br/>".format(global_pool)
            else:
                _pool.set_answer(" ".join(args))
                logger.info("Nr of winners: {}".format(len(_pool.winners)))
                if len(_pool.winners) == 0:
                    message = "No winner could be picked in Pool {}<br/>".format(pool_id)
                elif len(_pool.winners) == 1:
                    message = "There is a winner in Pool {}:<br/>{}<br/>"\
                                                 .format(pool_id, _pool.winners[0])
                else:
                    message = "There are multiple winners in Pool {}:<br/>{}<br/>"\
                        .format(pool_id, ", ".join(_pool.winners))

            message += _pool.print(True)
            yield from _poolbots.one2one(bot, event.user.id_.chat_id, message)

        elif cmd == 'announce':
            if not _pool.answer:
                html = "There is no answer yet for {}<br/>".format(_pool.name)
            else:
                _pool.set_open(False)
                _pool.set_secret(False)
                _poolbot.count_score(_pool)
                html = "<b>Announcing results of {}!</b><br/>".format(_pool.name)
                html += "The correct answer is {}<br/>".format(_pool.answer)
                if len(_pool.winners) == 0:
                    html += "\ud83d\udce3 No winner could be picked in Pool {}<br/><br/>".format(pool_id)
                elif len(_pool.winners) == 1:
                    html += "\ud83d\udce3 There is a winner in Pool {}:<br/>".format(pool_id)
                    html += "Congratulations, <b>{}</b>! \ud83c\udf87\ud83c\udf89<br/><br/>".format(_pool.winners[0])
                else:
                    html += "\u203c\ufe0f\ud83d\udce3 There are multiple winners in Pool {}:<br/><b>{}</b><br/>"\
                        .format(pool_id, ", ".join(_pool.winners))
                    html += "Congratulations all! \ud83c\udf87\ud83c\udf89<br/><br/>"

            html += _pool.print()
            html += _poolbot.print_score()
        elif cmd == 'remove':
            if not _poolbot.remove(pool_id):
                html = "Pool {} not found in conversation".format(pool_id)
        else:
            # send full info to private chat
            yield from _poolbots.one2one(bot, event.user.id_.chat_id, _pool.print(True))

        if html == "":
            html = _poolbot.print()
            html += "<br/>Type <i>/bot pool <nr> bet <your value></i> to bet.<br/>".format(pool_id)

    _poolbot.save(bot)
    _poolbots.save(bot)
    bot.memory.save()

    yield from bot.coro_send_message(event.conv_id, html)


def _initialise(bot):
    plugins.register_user_command(["pool"])
    plugins.register_admin_command(["poolbot"])
    _poolbots.load_pools(bot)

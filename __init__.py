import time, re, logging, plugins


class PollBots:
    def __init__(self):
        self.pollbots = {}

    def load_polls(self, bot):
        if bot.memory.exists(["pollsbot.polls"]):
            polls = bot.memory.get("pollsbot.polls")
            for pollbot_data in polls:
                self.pollbots[pollbot_data["conv_id"]] = PollBot(pollbot_data, bot)

    def get(self, bot, conv_id):
        if conv_id not in self.pollbots:
            pollbot_data = {'conv_id': conv_id}
            self.pollbots[conv_id] = PollBot(pollbot_data, bot)

        return self.pollbots[conv_id]

    def save(self, bot):
        pollbots_data = []
        for conv_id, _pollbot in self.pollbots.items():
            pollbots_data.append({
                'conv_id': _pollbot.conv_id
            })
        bot.memory.set_by_path(["pollsbot.polls"], pollbots_data)

    @staticmethod
    def one2one(bot, user_id, message):
        logger.info("{} unavailable for {}".format(message, user_id))
        target_conv = yield from bot.get_1to1(user_id)
        if not target_conv:
            logger.error("1-to-1 unavailable for {}".format(user_id))
            return False

        yield from bot.coro_send_message(target_conv, message)

    @staticmethod
    def user_in_conversation(bot, conv_id, user):
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


class PollBot:
    def __init__(self, pollbot_data, bot):
        self.bot = bot
        self.conv_id = pollbot_data["conv_id"]
        # polls from conv memory
        self.bot.initialise_memory(self.conv_id, "polls")
        self.bot.initialise_memory(self.conv_id, "polls_score")
        self.polls = []
        if self.bot.memory.exists(["polls", self.conv_id]):
            polls_data = bot.memory.get_by_path(["polls", self.conv_id])
            for poll_data in polls_data:
                self.create(poll_data)
        self.score = {}
        if self.bot.memory.exists(["polls_score", self.conv_id]):
            self.score = bot.memory.get_by_path(["polls_score", self.conv_id])

    def create(self, poll_data):
        self.polls.append(Poll(poll_data))

    def get(self, poll_id):
        try:
            return self.polls[(poll_id - 1)]
        except IndexError:
            return False

    def remove(self, poll_id):
        try:
            del self.polls[(poll_id - 1)]
            return True
        except IndexError:
            return False

    def count_score(self, _poll):
        if not _poll.final:
            for user_id, _bet in _poll.bets.items():
                score = 1 if _bet["name"] in _poll.winners else 0
                if _bet["name"] not in self.score:
                    self.score[_bet["name"]] = score
                else:
                    self.score[_bet["name"]] += score
            _poll.final = True

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
        html = "<b>Current polls:</b> <br />"
        poll_id = 1
        for _poll in self.polls:
            html += "poll {}: <b>{}</b><br />".format(poll_id, _poll.name, _poll.descr)
            if _poll.descr:
                html += "{}<br />".format(_poll.descr)
            if not _poll.open:
                html += " <b>(closed)</b>"
            if _poll.secret:
                html += " <b>(secret)</b>"
            html += "<br />"
            poll_id += 1
        return html

    def save(self, bot):
        polls_data = []
        for _poll in self.polls:
            polls_data.append({
                'name': _poll.name,
                'descr': _poll.descr,
                'answer': _poll.answer,
                'final': _poll.final,
                'open': _poll.open,
                'secret': _poll.secret,
                'winners': _poll.winners,
                'bets': _poll.bets,
            })
        bot.memory.set_by_path(["polls", self.conv_id], polls_data)


class Poll:
    def __init__(self, poll_data):
        self.name = poll_data["name"]
        self.descr = poll_data["descr"]
        self.answer = poll_data["answer"]
        self.open = poll_data["open"]
        self.final = poll_data["final"]
        self.secret = poll_data["secret"]
        self.winners = poll_data["winners"]
        self.bets = poll_data["bets"]

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

_pollbots = PollBots()

logger = logging.getLogger(__name__)


def poll(bot, event, poll_id=None, cmd=None, *args):
    html = ""
    extern_conv = False
    _pollbot = _pollbots.get(bot, event.conv_id)

    if poll_id == 'scores':
        html = _pollbots.get(bot, event.conv_id).print_score()
    elif poll_id == 'help':
        html = "<i>View the polls:</i><br/>/bot poll<br/>"
        html += "<i>View the scores:</i><br/>/bot poll scores<br/>"
        html += "<i>View current bets of poll:</i><br/>/bot poll <id><br/>"
        html += "<i>Place a bet for poll:</i><br/>/bot poll <id> bet (<value>)<br/>"
        html += "<i>This help:</i><br/>/bot poll help<br/>"
        html += "<i>More help:</i><br/>" \
                "<a href='https://github.com/malles/pollbot'>https://github.com/malles/pollbot</a><br/>"
    elif poll_id:
        try:
            poll_id.index("||")
            conv_id = poll_id[:poll_id.index("||")].strip()
            logger.info("Voting secretly for conv_id: {}".format(conv_id))
            poll_id = int(poll_id[poll_id.index("||") + 2:])
            if not _pollbots.user_in_conversation(bot, conv_id, event.user):
                yield from bot.coro_send_message(event.conv_id, "You are not in that conversation!")
                return

            extern_conv = True
            _pollbot = _pollbots.get(bot, conv_id)

        except ValueError:
            if _pollbots.is_int(poll_id):
                poll_id = int(poll_id)
            else:
                yield from bot.coro_send_message(event.conv_id, "Unknown command {}".format(poll_id))
                return

        _poll = _pollbot.get(poll_id)
        if not _poll:
            yield from bot.coro_send_message(event.conv_id, "Poll {} not found in conversation".format(poll_id))
            return

        if cmd == 'bet':
            if not _poll.open:
                html = "<b>This poll is closed for betting</b><br/>"
            elif _poll.secret and not extern_conv:
                global_poll = "{}||{}".format(event.conv_id, poll_id)
                message = "Type <i>/bot poll {} bet <value></i> in this chat to place your bet.".format(global_poll)
                yield from _pollbots.one2one(bot, event.user.id_.chat_id, message)
            else:
                _poll.set_bet(event.user, " ".join(args))
                if extern_conv or not _poll.secret:
                    html += "<b>Your bet has been set:</b><br/> {}<br/>".format(" ".join(args))
                    html += _poll.print()

        else:
            html = _poll.print()
            if _poll.open:
                html += "<br/>Type <i>/bot poll {} bet</i> to bet.<br/>"\
                    .format(poll_id, '' if _poll.secret else ' <your value>')
    else:
        html = _pollbot.print()
        html += "<br/>Type <i>/bot poll <nr> bet <your value></i> to bet.<br/>".format(poll_id)

    _pollbot.save(bot)
    _pollbots.save(bot)
    bot.memory.save()
    yield from bot.coro_send_message(event.conv_id, html)


def pollbot(bot, event, poll_id=None, cmd=None, *args):
    html = ""
    extern_conv = False
    _pollbot = _pollbots.get(bot, event.conv_id)

    if poll_id == 'reset_scores':
        _pollbot.reset_scores()
        html = _pollbots.get(bot, event.conv_id).print_score()
    if poll_id == 'clear_scores':
        _pollbot.clear_scores()
        html = _pollbots.get(bot, event.conv_id).print_score()
    elif poll_id == 'create':
        name = cmd
        _pollbot.create({
            'name': name,
            'descr': " ".join(args),
            'answer': False,
            'open': True,
            'final': False,
            'secret': False,
            'winners': [],
            'bets': {}
        })
        html = _pollbot.print()
        _pollbot.save(bot)
    elif poll_id == 'help':
        html = "<i>Create a poll:</i><br/>/bot pollbot create <name> <descr><br/>"
        html += "<i>Set description:</i><br/>/bot pollbot <id> descr <description><br/>"
        html += "<i>Set to secret:</i><br/>/bot pollbot <id> secret<br/>"
        html += "<i>Set to public:</i><br/>/bot pollbot <id> public<br/>"
        html += "<i>Close poll:</i><br/>/bot pollbot <id> close<br/>"
        html += "<i>Re-open poll:</i><br/>/bot pollbot <id> open<br/>"
        html += "<i>Remove poll:</i><br/>/bot pollbot <id> remove<br/>"
        html += "<i>Set answer:</i><br/>/bot pollbot <id> answer <answer><br/>"
        html += "<i>Set winner manually:</i><br/>/bot pollbot <id> winner <winnerslist><br/>"
        html += "<i>Announce winner:</i><br/>/bot pollbot <id> announce<br/>"
        html += "<i>This help:</i><br/>/bot poll help<br/>"
        html += "<i>More help:</i><br/>" \
                "<a href='https://github.com/malles/pollbot'>https://github.com/malles/pollbot</a><br/>"
    elif poll_id:
        try:
            poll_id.index("||")
            conv_id = poll_id[:poll_id.index("||")].strip()
            logger.info("Voting secretly for conv_id: {}".format(conv_id))
            poll_id = int(poll_id[poll_id.index("||") + 2:])
            if not _pollbots.user_in_conversation(bot, conv_id, event.user):
                yield from bot.coro_send_message(event.conv_id, "You are not in that conversation!")
                return

            extern_conv = True
            _pollbot = _pollbots.get(bot, conv_id)

        except ValueError:

            if _pollbots.is_int(poll_id):
                poll_id = int(poll_id)
            else:
                yield from bot.coro_send_message(event.conv_id, "Unknown command {}".format(poll_id))
                return

        _poll = _pollbot.get(poll_id)
        if not _poll:
            yield from bot.coro_send_message(event.conv_id, "Poll {} not found in conversation".format(poll_id))
            return

        if cmd == 'descr':
            _poll.set_descr(" ".join(args))
        elif cmd == 'open':
            _poll.set_open(True)
        elif cmd == 'close':
            _poll.set_open(False)
        elif cmd == 'secret':
            _poll.set_secret(True)
        elif cmd == 'public':
            _poll.set_secret(False)
        elif cmd == 'winner':
            if not extern_conv and not len(args):
                global_poll = "{}||{}".format(event.conv_id, poll_id)
                message = "Type <i>/bot pollbot {} winner <value></i> in this chat to set winner.".format(global_poll)
            else:
                _poll.set_winner(" ".join(args))
                if len(_poll.winners) == 0:
                    message = "No winner could be picked in Poll {}<br/>".format(_poll.name)
                else:
                    message = "Winners set for Poll {}: {}<br/>".format(_poll.name, ", ".join(_poll.winners))

            message += _poll.print(True)
            yield from _pollbots.one2one(bot, event.user.id_.chat_id, message)

        elif cmd == 'answer':
            if not extern_conv and not len(args):
                global_poll = "{}||{}".format(event.conv_id, poll_id)
                message = "Type <i>/bot pollbot {} answer <value></i> in this chat to set answer.<br/>".format(global_poll)
            else:
                _poll.set_answer(" ".join(args))
                logger.info("Nr of winners: {}".format(len(_poll.winners)))
                if len(_poll.winners) == 0:
                    message = "No winner could be picked in Poll {}<br/>".format(poll_id)
                elif len(_poll.winners) == 1:
                    message = "There is a winner in Poll {}:<br/>{}<br/>"\
                                                 .format(poll_id, _poll.winners[0])
                else:
                    message = "There are multiple winners in Poll {}:<br/>{}<br/>"\
                        .format(poll_id, ", ".join(_poll.winners))

            message += _poll.print(True)
            yield from _pollbots.one2one(bot, event.user.id_.chat_id, message)

        elif cmd == 'announce':
            if not _poll.answer:
                html = "There is no answer yet for {}<br/>".format(_poll.name)
            else:
                _poll.set_open(False)
                _poll.set_secret(False)
                _pollbot.count_score(_poll)
                html = "<b>Announcing results of {}!</b><br/>".format(_poll.name)
                html += "The correct answer is {}<br/>".format(_poll.answer)
                if len(_poll.winners) == 0:
                    html += "\ud83d\udce3 No winner could be picked in Poll {}<br/><br/>".format(poll_id)
                elif len(_poll.winners) == 1:
                    html += "\ud83d\udce3 There is a winner in Poll {}:<br/>".format(poll_id)
                    html += "Congratulations, <b>{}</b>! \ud83c\udf87\ud83c\udf89<br/><br/>".format(_poll.winners[0])
                else:
                    html += "\u203c\ufe0f\ud83d\udce3 There are multiple winners in Poll {}:<br/><b>{}</b><br/>"\
                        .format(poll_id, ", ".join(_poll.winners))
                    html += "Congratulations all! \ud83c\udf87\ud83c\udf89<br/><br/>"

            html += _poll.print()
            html += _pollbot.print_score()
        elif cmd == 'remove':
            if not _pollbot.remove(poll_id):
                html = "Poll {} not found in conversation".format(poll_id)
        else:
            # send full info to private chat
            yield from _pollbots.one2one(bot, event.user.id_.chat_id, _poll.print(True))

        if html == "":
            html = _pollbot.print()
            html += "<br/>Type <i>/bot poll <nr> bet <your value></i> to bet.<br/>".format(poll_id)

    _pollbot.save(bot)
    _pollbots.save(bot)
    bot.memory.save()

    yield from bot.coro_send_message(event.conv_id, html)


def _initialise(bot):
    plugins.register_user_command(["poll"])
    plugins.register_admin_command(["pollbot"])
    _pollbots.load_polls(bot)

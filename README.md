# Hangoutsbot Poll plugin

Hangoutsbot plugin to create Polls and quizzes in your Hangout. Keep a general score over all polls.


## Installation and config

Copy the `pollbot` folder into the folder `hangupsbot/plugins` in your installation. Do it manually, or use GIT for easy updating:

From your `hangoutsbot` folder:
```
git clone https://github.com/malles/pollbot ./hangupsbot/plugins/pollbot
```

Then just add `"pollbot"` to your plugins list in the config.json file.

All polls and results are managed from the chats. Acces polls form a chat directly in that chat, or get remote key for setting up bets/answers/winners in one 2 one chat privately.

## User tasks

`.bot poll` for user tasks

### View polls
`/bot poll`
The bot replies with the list of current polls

```
/bot poll

    Current polls:
    poll 1: AP-rush
    How many AP wil agent Y score today

    Type /bot poll <nr> bet <your value> to bet.
```
The polls can be accessed by referring to the number of the poll in this list.

### View bets
`/bot poll 1`
Where poll_id is the number as shown in the current poll-list. The bot replies with the list of bets of the requested poll. Only visible for public polls

```
/bot poll 1

    AP-rush
    How many AP wil agent Y score today
    Current bets:
    Charles Darwin: 22500
```

### Place bet
`/bot poll 1 bet (<value>)`
Where poll_id is the number as shown in the current poll-list. For secret polls leave out the value in the main chat! You will recieve the chat-id needed to set the value in the one 2 one chat.

*Public poll*
```
/bot poll 1 bet 34523

    Your bet has been set:
    34523
    AP-rush
    How many AP wil agent Y score today
    Current bets:
    John Doe: 34523
    Charles Darwin: 22500
```
*Secret poll*
```
/bot poll 1 bet

    (private chat)
    Type /bot poll UgxJF7fRXig-McA3VCN4AaABAagBh73LBQ||1 bet <value> in this chat to to place your bet.
```
You can then set the bet using that poll-id:
`/bot pollbot UgxJF7fRXig-McA3VCN4AaABAagBh73LBQ||1 bet 34523`
The bot will reply as above with the public poll.

### View scores
`/bot poll scores`
Once a winner is announced, the totals are tallied in a score-list.

```
/bot poll scores

    Current scores:
    John Doe: 0
    Charles Darwin: 1
```

## Admin tasks

`.bot pollbot` for admin tasks

### Create Poll
`/bot pollbot create <name> <descr>`
Where name is one word, or phrase in `"` quotes, and description the following sentence. The bot will reply with a list of current polls

```
/bot pollbot create AP-rush How many AP wil agent X score today

    Current polls:
    poll 1: AP-rush
    How many AP wil agent X score today
```

The polls can be accessed by referring to the number of the poll in this list. This is used to bet for and manage the poll.

### Change description
`/bot pollbot <poll_id> <descr>`
Where poll_id is the number as shown in the current poll-list, and description the following sentence. The bot will reply with the list of current polls

```
/bot pollbot 1 descr How many AP wil agent Y score today

    Current polls:
    poll 1: AP-rush
    How many AP wil agent Y score today
```

### View bets
`/bot pollbot <poll_id>`
The bot will reply with the list of current bets in a one 2 one chat.

```
/bot pollbot 1

    AP-rush
    How many AP wil agent Y score today
    Current bets:
    John Doe: 34523
    Charles Darwin: 22500
```

### Poll options
`/bot pollbot <poll_id> <command>`
Polls can be closed or opened for betting, and can be private or public. In private Polls all players will vote via a one 2 one chat with the bot, via the chat-id they get in the main chat.
By default polls are opened and public.

```
/bot pollbot 1 open
/bot pollbot 1 close
/bot pollbot 1 public
/bot pollbot 1 secret

```

### Set answer
`/bot pollbot <poll_id> answer (<answer>)`
Set the correct answer for the poll. For secret polls leave out the answer in the main chat! You will recieve the chat-id needed to set the answer in the one 2 one chat.
On setting the answer the bot will try to automatically find players with the correct answer and report that back via one 2 one chat. A full list of bets is shown as well.

*Public poll*
```
/bot pollbot 1 answer 24598

    (private chat)
    No winner could be picked in Poll 1
    AP-rush
    How many AP wil agent Y score today
    Current bets:
    John Doe: 34523
    Charles Darwin: 22500
```
In the main chat the current polls will be shown.

*Secret poll*
```
/bot pollbot 1 answer

    (private chat)
    Type /bot pollbot UgxJF7fRXig-McA3VCN4AaABAagBh73LBQ||1 answer <value> in this chat to set answer.
    AP-rush
    How many AP wil agent Y score today
    Current bets:
    John Doe: 34523
    Charles Darwin: 22500
```
You can then set the answer using that poll-id:
`/bot pollbot UgxJF7fRXig-McA3VCN4AaABAagBh73LBQ||1 answer 24598`
The bot will reply as above with the public poll with the winners and bets.

### Set winners
`/bot pollbot <poll_id> winner (<winner>)`
When no winner is automatically selected (perfect match), you can optionally set a winner manually. For instance based on approximation or sheer bias. For secret polls leave out the winner in the main chat! You will recieve the chat-id needed to set the winner in the one 2 one chat.

```
/bot pollbot 1 winner Charles Darwin

    (private chat)
    Winners set for Poll AP-rush: Charles Darwin
    AP-rush
    How many AP wil agent Y score today
    Current bets:
    John Doe: 34523
    Charles Darwin: 22500
```
A poll can have multiple winners. Make sure a list of all full names of winners is mentioned after 'winner'.
```
/bot pollbot 1 winner John Doe, Charles Darwin

    (private chat)
    Winners set for Poll AP-rush: John Doe, Charles Darwin
    AP-rush
    How many AP wil agent Y score today
    Current bets:
    John Doe: 34523
    Charles Darwin: 22500
```

### Announce winners
`/bot pollbot <poll_id> announce`
When the answer is set and the winner has been chosen, the bot can announce the result in the main chat and tally up the global scores. A poll can have no winners, and no points are added to the scores.
The chat will automatically close and be public after announcing the winner.

```
/bot pollbot 1 announce

    Announcing results of AP-rush!
    The correct answer is 24598
    📣 There is a winner in Poll 1:
    Congratulations, Charles Darwin! 🎇🎉

    AP-rush
    How many AP wil agent Y score today
    closed
    Current bets:
    John Doe: 34523
    Charles Darwin: 22500
    Current scores:
    John Doe: 0
    Charles Darwin: 1

```

### Reset scores
`/bot pollbot reset_scores`
Sets the score of all players in the score-list to 0.

### Clear scores
`/bot pollbot clear_scores`
Completely clears the score-list and the players.

### Remove poll
`/bot pollbot <poll_id> remove`
Removes a poll from memory. Beware that the poll-ids in the list will shift!

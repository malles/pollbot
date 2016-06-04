# Hangoutsbot Pool plugin

Hangoutsbot plugin to create Pools and quizes in your Hangout. Keep a general score over all pools.


## Installation and config

Copy the `poolbot` folder into the folder `hangupsbot/plugins` in your installation. Do it manually, or use GIT for easy updating:

From your `hangoutsbot` folder:
```
git clone https://github.com/malles/poolbot ./hangupsbot/plugins/poolbot
```

Then just add `"poolbot"` to your plugins list in the config.json file.

All pools and results are managed from the chats. Acces pools form a chat directly in that chat, or get remote key for setting up bets/answers/winners in one 2 one chat privately.

## User tasks

`.bot pool` for user tasks

### View pools
`/bot pool`
The bot replies with the list of current pools

```
/bot pool

    Current pools:
    pool 1: AP-rush
    How many AP wil agent Y score today

    Type /bot pool <nr> bet <your value> to bet.
```
The pools can be accessed by referring to the number of the pool in this list.

### View bets
`/bot pool 1`
Where pool_id is the number as shown in the current pool-list. The bot replies with the list of bets of the requested pool. Only visible for public pools

```
/bot pool 1

    AP-rush
    How many AP wil agent Y score today
    Current bets:
    Charles Darwin: 22500
```

### Place bet
`/bot pool 1 bet (<value>)`
Where pool_id is the number as shown in the current pool-list. For secret pools leave out the value in the main chat! You will recieve the chat-id needed to set the value in the one 2 one chat.

*Public pool*
```
/bot pool 1 bet 34523

    Your bet has been set:
    34523
    AP-rush
    How many AP wil agent Y score today
    Current bets:
    John Doe: 34523
    Charles Darwin: 22500
```
*Secret pool*
```
/bot pool 1 bet

    (private chat)
    Type /bot pool UgxJF7fRXig-McA3VCN4AaABAagBh73LBQ||1 bet <value> in this chat to to place your bet.
```
You can then set the bet using that pool-id:
`/bot poolbot UgxJF7fRXig-McA3VCN4AaABAagBh73LBQ||1 bet 34523`
The bot will reply as above with the public pool.

### View scores
`/bot pool scores`
Once a winner is announced, the totals are tallied in a score-list.

```
/bot pool scores

    Current scores:
    John Doe: 0
    Charles Darwin: 1
```

## Admin tasks

`.bot poolbot` for admin tasks

### Create Pool
`/bot poolbot create <name> <descr>`
Where name is one word, or phrase in `"` quotes, and description the following sentence. The bot will reply with a list of current pools

```
/bot poolbot create AP-rush How many AP wil agent X score today

    Current pools:
    pool 1: AP-rush
    How many AP wil agent X score today
```

The pools can be accessed by referring to the number of the pool in this list. This is used to bet for and manage the pool.

### Change description
`/bot poolbot <pool_id> <descr>`
Where pool_id is the number as shown in the current pool-list, and description the following sentence. The bot will reply with the list of current pools

```
/bot poolbot 1 descr How many AP wil agent Y score today

    Current pools:
    pool 1: AP-rush
    How many AP wil agent Y score today
```

### View bets
`/bot poolbot <pool_id>`
The bot will reply with the list of current bets in a one 2 one chat.

```
/bot poolbot 1

    AP-rush
    How many AP wil agent Y score today
    Current bets:
    John Doe: 34523
    Charles Darwin: 22500
```

### Pool options
`/bot poolbot <pool_id> <command>`
Pools can be closed or opened for betting, and can be private or public. In private Pools all players will vote via a one 2 one chat with the bot, via the chat-id they get in the main chat.
By default pools are opened and public.

```
/bot poolbot 1 open
/bot poolbot 1 close
/bot poolbot 1 public
/bot poolbot 1 secret

```

### Set answer
`/bot poolbot <pool_id> answer (<answer>)`
Set the correct answer for the pool. For secret pools leave out the answer in the main chat! You will recieve the chat-id needed to set the answer in the one 2 one chat.
On setting the answer the bot will try to automatically find players with the correct answer and report that back via one 2 one chat. A full list of bets is shown as well.

*Public pool*
```
/bot poolbot 1 answer 24598

    (private chat)
    No winner could be picked in Pool 1
    AP-rush
    How many AP wil agent Y score today
    Current bets:
    John Doe: 34523
    Charles Darwin: 22500
```
In the main chat the current pools will be shown.

*Secret pool*
```
/bot poolbot 1 answer

    (private chat)
    Type /bot poolbot UgxJF7fRXig-McA3VCN4AaABAagBh73LBQ||1 answer <value> in this chat to set answer.
    AP-rush
    How many AP wil agent Y score today
    Current bets:
    John Doe: 34523
    Charles Darwin: 22500
```
You can then set the answer using that pool-id:
`/bot poolbot UgxJF7fRXig-McA3VCN4AaABAagBh73LBQ||1 answer 24598`
The bot will reply as above with the public pool with the winners and bets.

### Set winners
`/bot poolbot <pool_id> winner (<winner>)`
When no winner is automatically selected (perfect match), you can optionally set a winner manually. For instance based on approximation or sheer bias. For secret pools leave out the winner in the main chat! You will recieve the chat-id needed to set the winner in the one 2 one chat.

```
/bot poolbot 1 winner Charles Darwin

    (private chat)
    Winners set for Pool AP-rush: Charles Darwin
    AP-rush
    How many AP wil agent Y score today
    Current bets:
    John Doe: 34523
    Charles Darwin: 22500
```
A pool can have multiple winners. Make sure a list of all full names of winners is mentioned after 'winner'.
```
/bot poolbot 1 winner John Doe, Charles Darwin

    (private chat)
    Winners set for Pool AP-rush: John Doe, Charles Darwin
    AP-rush
    How many AP wil agent Y score today
    Current bets:
    John Doe: 34523
    Charles Darwin: 22500
```

### Announce winners
`/bot poolbot <pool_id> announce`
When the answer is set and the winner has been chosen, the bot can announce the result in the main chat and tally up the global scores. A pool can have no winners, and no points are added to the scores.
The chat will automatically close and be public after announcing the winner.

```
/bot poolbot 1 announce

    Announcing results of AP-rush!
    The correct answer is 24598
    📣 There is a winner in Pool 1:
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
`/bot poolbot reset_scores`
Sets the score of all players in the score-list to 0.

### Clear scores
`/bot poolbot clear_scores`
Completely clears the score-list and the players.

### Remove pool
`/bot poolbot <pool_id> remove`
Removes a pool from memory. Beware that the pool-ids in the list will shift!

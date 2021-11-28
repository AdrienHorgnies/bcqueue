# Blockchain queue

Simulation of a proof-of-work blockchain system using a MAP/PH/1 queue. It also provides an M/M/1 queue for comparison.

It is meant to be a computation model for the mathematical model developed by Quan-Lin Li, Jing-Yu Ma, Yan-Xia Chang,
Fan-Qi Ma & Hai-Bo Yu in "Markov processes in blockchain systems". Find it at https://doi.org/10.1186/s40649-019-0066-1.

For more information about this work, please read the accompanying thesis.

## Model

The queue is a two steps batch process :

- Infinite size waiting room. Service in random order.
- First step is called "transactions selection" or "block selection", the server randomly selects as many transactions
  as it can from the waiting room, with a maximum number of *b* transactions. The set of selected transactions is then
  called a "block".
- Second step is called "block mining". The server takes the block formed in the previous step and "mines" it. Once this
  step is done, the transactions definitely leaves the queue.
- The first and second steps are mutually exclusive and follow each other without interruption.

The queue comes in two version : M/M/1 (CLI option `--mm1`) or MAP/PH/1 (CLI option `--mapph1`).

## Parameters

All parameters must be provided in a folder :

- Either named "parameters" in the directory where you run the script.
- Or the folder path is given as the first command line argument.

All parameters are defined in their own csv file with the name of the parameter as the filename plus the
extension `.csv`. For examples, see the `parameters` folder this repository contains.

Both versions of the queue requires the following parameters :

- b : The max number of transactions a block can contain.
- tau : The time at which the simulation stops recording new transactions.

The M/M/1 queue requires the following parameters :

- lambda : The expected interarrival time.
- mu1 : The expected "transactions selection" duration.
- mu2 : The expected "block mining" duration.

The MAP/PH/1 queue requires the following parameters :

- C : Square matrix to generate the MAP process (non-absorbing transitions).
- D : Square matrix, same size as C, to generate the MAP process (absorbing transitions).
- omega : Vector of the stationary probabilities of the initial state of the MAP process.
- S : Square matrix to generate the PH process for the block selection.
- beta : Vector of the absorbing transitions probabilities for block selection (length equal to one side of S).
- T : Square matrix to generate the PH process for the block mining.
- alpha : Vector of the absorbing transitions probabilities for the block mining (length equal to one side of T).

## Measures

The measures are taken from tau / 2 to tau. Only the transactions arrivals, and blocks selection comprised in this
interval are taken into consideration. Furthermore, the queue continues running for up to ten expected block times after
tau. No late blocks or transactions are used for the measures, but it lets on-time transaction exit the queue.

All measures greater than ten expected block times are aggregated.

- The confirmation time : Which is also the sojourn time, is the time between the arrival of a transaction, and the time
  it leaves. From a blockchain point of view, it corresponds to the time between the broadcast of the transaction and
  the embedding of a block containing this transaction in the blockchain.
- The waiting time : The time between the arrival and the selection of a transaction.
- The service time : The time a transaction spends into the server.
- The block time : The time between successive blocks mining time.
- The block size : The number of transactions per block
- The waiting room size : The number of transactions in the waiting room.

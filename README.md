# Blockchain queue

Simulation of a proof-of-work blockchain system using a MAP/PH/1 queue.
It also provides an M/M/1 queue for comparison.

It is meant to be a computation model for the mathematical model developed by Quan-Lin Li, Jing-Yu Ma, Yan-Xia Chang, Fan-Qi Ma & Hai-Bo Yu  in "Markov processes in blockchain systems".
Find it at https://doi.org/10.1186/s40649-019-0066-1.

## Model
The queue is a two steps batch process :

- Infinite size waiting room. Service in random order.
- First step is called "transactions selection",
  the server randomly selects as many transactions as it can,
  with a maximum number of *b* transactions.
  The set of selected transactions is then called a "block".
- Second step is called "block mining".
  The server takes the block formed in the previous step and "mines" it.
  Once this step is done, the transactions definitely leaves the queue.
- The first and second steps are mutually exclusive and follow each other without interruption. 

The transactions arrive according to a MAP process defined by *C*, *D* and *omega*.
The "transactions selection" step service time is defined by a Phase-Type process defined by *S* and *beta*.
The "block mining" step service time is defined by a Phase-Type process defined by *T* and *alpha*.



## Parameters

The MAP/PH/1 queue requires the following parameters :

- C : Square matrix to generate the MAP process (non-absorbing transitions).
- D : Square matrix to generate the MAP process (absorbing transitions).
- omega : Vector of the stationary probabilities of the initial state of the MAP process.
- S : Square matrix to generate the PH process for the block selection.
- beta : Vector of the absorbing transitions probabilities for block selection.
- T : Square matrix to generate the PH process for the block mining.
- alpha : Vector of the absorbing transitions probabilities for block mining.

                                                       S=[[-10, 0],
                                                          [0, -10]],
                                                       b=[0.5, 0.5],
                                                       T=[[-590, 0],
                                                          [0, -590]],
                                                       a=[0.5, 0.5], 


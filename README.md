# BSAS

The BSAS recommends a consensus speed to a fleet of vehicles traveling along an extra-urban route (e.g., a highway), which contains a roal as **operator** and several **users**.

Users preprocess the speed-emission mappings using Shamir’s secret sharing algorithm. The operator downloads all shared speed-emission mappings and calculates the total emission value of all vehicles corresponding to each speed. The operator then gives the speed with the lowest emission value as the recommended speed. Users update their local vehicle speeds individually with the recommended speed.

## Roles

- **User:**  In BSAS, a user represents a vehicle that is willing to participate in the speed recommendation to obtain a consensus speed. 
- **operator:** Similar to miners in BitCoin, operators are incented to process transactions. 

## Procedures

- Users preprocess the speed-emission mappings using Shamir’s secret sharing algorithm.
- Each user generates transactions by attaching her shared mappings to the *trading* contract.
- operators download all shared speed-emission mappings from the *trading* contract.
- operators calculate the total emission value corresponding to each speed, give the speed with the lowest emission value as the recommended speed,  and upload the recommended speed to the *processing* contract.
- The *processing* contract sends the recommended speed to the *trading* contract.
- Users update their local vehicle speeds individually with the recommended speed returned by the *trading* contract.

## Pre-Requisites

You will need the following installed on your machine before you can start:

- [Ubuntu 18.04](https://ubuntu.com/download/alternative-downloads)
- [Geth 1.10.8](https://geth.ethereum.org/downloads/)
- [Python 3.6.9](https://www.python.org/downloads/)
- Ganache-cli
- Web3
- Truffle

## Getting Set Up

To get started, clone this repository with:

    git clone https://github.com/BSAS-ieee/BSAS

And change directories to the newly cloned repo:

    cd CODE

 ## Steps

### **1. Accounts generation**

```
ganache-cli -a 16
```

**Modify:** Number of accounts. Generate a valid account for each user and processor.

### **2. Smart Contracts Compilation**

```
truffle compile
```

**Note:** Open a new terminal and run this command.

### **3. Smart Contracts Migration**

```
truffle migrate
```

**Note:** Record the contract address of the smart contracts.

### **4. Secret sharing & Speed recommendation**

```
cd pythonProject
```

```
sudo python Demo.py
```

**Modify:** [w3(Web3.HTTPProvider)],  [cars_num], [TRADING_CONTRACT_ADDR ],[PROCESSING_CONTRACT_ADDR ], [self.web3(Web3.WebsocketProvider)], [the path of compiled smart contracts].


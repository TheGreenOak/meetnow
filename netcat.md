# Netcat Proof of Concept

This proof of concept attempts to demonstrate a very basic peer to peer text communication between two peers without the use of signaling servers.

## How to perform it
- Grab your public IP from a STUN service (like ip8.com)
- Send it to your peer, and get their IP address (via any means)
- Coordinate a netcat connection, by typing the following:
  - On Peer A: `netcat -p 7777 [Peer B's IP] 8888`
  - On Peer B: `netcat -p 8888 [Peer A's IP] 7777`

## How it works
Essentially, what you've done is called "TCP Hole-punching". By sending a packet from port 7777 (for instance), you've "opened" port 7777, and forced your NAT to provide you with any communication coming out of this port.

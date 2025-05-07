# API Documentation

This document provides information about the RESTful API endpoints available in the blockchain system.

## Base URL

All API endpoints are available at:

```
http://localhost:5000/api/v1
```

For production environments, it's recommended to use HTTPS:

```
https://your-node.example.com/api/v1
```

## Authentication

Some endpoints require authentication using JSON Web Tokens (JWT). To authenticate:

1. Obtain a token using the `/auth/login` endpoint
2. Include the token in the `Authorization` header:

```
Authorization: Bearer <your_token>
```

## Endpoints

### Blockchain Information

#### Get Blockchain Status

```
GET /status
```

Returns the current status of the blockchain including height, difficulty, and mining rate.

**Response:**
```json
{
  "height": 142,
  "difficulty": 4,
  "blocks_count": 142,
  "last_block_time": "2023-06-15T14:23:55Z",
  "average_block_time": 602.4,
  "current_difficulty": 4,
  "peers_count": 5
}
```

#### Get Block By Height

```
GET /blocks/{height}
```

Returns details of a specific block by its height.

**Parameters:**
- `height`: Block height (integer)

**Response:**
```json
{
  "index": 142,
  "timestamp": "2023-06-15T14:23:55Z",
  "transactions": [
    {
      "sender": "0x3f4d9...",
      "recipient": "0x8a72c...",
      "amount": 5.0,
      "timestamp": "2023-06-15T14:23:35Z",
      "signature": "3045..."
    }
  ],
  "previous_hash": "00000a5c9...",
  "nonce": 24836,
  "hash": "00000bcd1..."
}
```

#### Get Block By Hash

```
GET /blocks/hash/{hash}
```

Returns details of a specific block by its hash.

**Parameters:**
- `hash`: Block hash (string)

**Response:** Same as Get Block By Height

#### Get Latest Blocks

```
GET /blocks/latest?limit={limit}
```

Returns the most recent blocks in the blockchain.

**Parameters:**
- `limit`: Number of blocks to return (default: 10, max: 100)

**Response:**
```json
{
  "blocks": [
    {
      "index": 142,
      "timestamp": "2023-06-15T14:23:55Z",
      "transactions_count": 3,
      "previous_hash": "00000a5c9...",
      "hash": "00000bcd1..."
    },
    // More blocks...
  ],
  "count": 10,
  "total_blocks": 142
}
```

### Transactions

#### Create Transaction

```
POST /transactions
```

Creates a new transaction and adds it to the pending transactions pool.

**Request:**
```json
{
  "sender": "0x3f4d9...",
  "recipient": "0x8a72c...",
  "amount": 5.0,
  "private_key": "5a4e2..." // Note: In a real implementation, signing should be done client-side
}
```

**Response:**
```json
{
  "success": true,
  "transaction": {
    "sender": "0x3f4d9...",
    "recipient": "0x8a72c...",
    "amount": 5.0,
    "timestamp": "2023-06-15T14:25:12Z",
    "signature": "3045..."
  },
  "message": "Transaction added to the pool"
}
```

#### Get Pending Transactions

```
GET /transactions/pending
```

Returns all transactions currently in the pending pool.

**Response:**
```json
{
  "transactions": [
    {
      "sender": "0x3f4d9...",
      "recipient": "0x8a72c...",
      "amount": 5.0,
      "timestamp": "2023-06-15T14:25:12Z",
      "signature": "3045..."
    },
    // More transactions...
  ],
  "count": 3
}
```

#### Get Transaction By Signature

```
GET /transactions/{signature}
```

Returns details of a specific transaction by its signature.

**Parameters:**
- `signature`: Transaction signature (string)

**Response:**
```json
{
  "transaction": {
    "sender": "0x3f4d9...",
    "recipient": "0x8a72c...",
    "amount": 5.0,
    "timestamp": "2023-06-15T14:20:30Z",
    "signature": "3045...",
    "block_height": 141,
    "confirmations": 1
  }
}
```

### Wallet

#### Create Wallet

```
POST /wallet
```

Creates a new wallet.

**Response:**
```json
{
  "address": "0x8a72c...",
  "public_key": "0482a...",
  "private_key": "5a4e2..." // Note: Private key should only be shown once
}
```

#### Get Wallet Balance

```
GET /wallet/{address}/balance
```

Returns the current balance of a wallet.

**Parameters:**
- `address`: Wallet address (string)

**Response:**
```json
{
  "address": "0x8a72c...",
  "balance": 125.5,
  "pending_balance": 5.0,
  "transactions_count": 12
}
```

#### Get Wallet Transactions

```
GET /wallet/{address}/transactions?limit={limit}&offset={offset}
```

Returns transactions associated with a specific wallet.

**Parameters:**
- `address`: Wallet address (string)
- `limit`: Number of transactions to return (default: 10, max: 100)
- `offset`: Pagination offset (default: 0)

**Response:**
```json
{
  "address": "0x8a72c...",
  "transactions": [
    {
      "sender": "0x3f4d9...",
      "recipient": "0x8a72c...",
      "amount": 5.0,
      "timestamp": "2023-06-15T14:20:30Z",
      "signature": "3045...",
      "block_height": 141
    },
    // More transactions...
  ],
  "count": 10,
  "total": 12
}
```

### Mining

#### Start Mining

```
POST /mining/start
```

Starts the mining process on the node.

**Authentication Required**

**Response:**
```json
{
  "success": true,
  "message": "Mining process started"
}
```

#### Stop Mining

```
POST /mining/stop
```

Stops the mining process on the node.

**Authentication Required**

**Response:**
```json
{
  "success": true,
  "message": "Mining process stopped"
}
```

#### Get Mining Status

```
GET /mining/status
```

Returns the current mining status of the node.

**Response:**
```json
{
  "is_mining": true,
  "hash_rate": "45.2 H/s",
  "pending_transactions": 3,
  "current_difficulty": 4
}
```

### Network

#### Get Peers

```
GET /network/peers
```

Returns a list of connected peers.

**Authentication Required**

**Response:**
```json
{
  "peers": [
    {
      "node_id": "a1b2c3...",
      "address": "192.168.1.100",
      "port": 6000,
      "last_seen": "2023-06-15T14:26:42Z",
      "latency": 45
    },
    // More peers...
  ],
  "count": 5
}
```

#### Add Peer

```
POST /network/peers
```

Adds a new peer to the network.

**Authentication Required**

**Request:**
```json
{
  "address": "192.168.1.101",
  "port": 6000
}
```

**Response:**
```json
{
  "success": true,
  "message": "Peer added successfully",
  "peer": {
    "node_id": "d4e5f6...",
    "address": "192.168.1.101",
    "port": 6000
  }
}
```

### Authentication

#### Login

```
POST /auth/login
```

Authenticates a user and returns a JWT token.

**Request:**
```json
{
  "address": "0x8a72c...",
  "signature": "3045..." // Signature of a challenge value
}
```

**Response:**
```json
{
  "token": "eyJhbGc...",
  "expires_at": "2023-06-16T14:30:42Z"
}
```

## Error Handling

All API endpoints return standard HTTP status codes:

- `200 OK`: The request was successful
- `201 Created`: The resource was created successfully
- `400 Bad Request`: The request was invalid
- `401 Unauthorized`: Authentication is required or failed
- `403 Forbidden`: The authenticated user doesn't have permission
- `404 Not Found`: The requested resource was not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: An error occurred on the server

Error responses have the following format:

```json
{
  "error": true,
  "code": "TRANSACTION_VALIDATION_FAILED",
  "message": "Transaction signature is invalid",
  "details": {
    "field": "signature",
    "reason": "Invalid format"
  }
}
```

## Rate Limiting

API requests are rate-limited to protect the service from abuse. Rate limits are applied per IP address and per API key (if authenticated).

Default rate limits:
- Unauthenticated requests: 60 requests per minute
- Authenticated requests: 300 requests per minute

Rate limit headers are included in the response:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 58
X-RateLimit-Reset: 1686836442
```

## Versioning

The API is versioned using URL path versioning (e.g., `/api/v1`). When a new version is released, the previous version will be maintained for a transition period.

## Webhooks

The API supports webhooks for receiving real-time notifications about blockchain events:

```
POST /webhooks
```

**Authentication Required**

**Request:**
```json
{
  "url": "https://your-service.com/blockchain-events",
  "events": ["new_block", "new_transaction"],
  "secret": "your_webhook_secret"
}
```

**Response:**
```json
{
  "id": "wh_123abc",
  "url": "https://your-service.com/blockchain-events",
  "events": ["new_block", "new_transaction"],
  "created_at": "2023-06-15T14:30:00Z"
}
```

## Example Usage

### Example: Creating and Mining a Transaction

1. Create a wallet:

```bash
curl -X POST http://localhost:5000/api/v1/wallet
```

2. Create a transaction:

```bash
curl -X POST http://localhost:5000/api/v1/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "0x3f4d9...",
    "recipient": "0x8a72c...",
    "amount": 5.0,
    "private_key": "5a4e2..."
  }'
```

3. Start mining (if not already running):

```bash
curl -X POST http://localhost:5000/api/v1/mining/start \
  -H "Authorization: Bearer eyJhbGc..."
```

4. Check transaction status:

```bash
curl -X GET http://localhost:5000/api/v1/transactions/3045...
```

## SDK Libraries

We provide official SDK libraries for easy integration with the blockchain API:

- JavaScript/Node.js: [blockchain-js-sdk](https://github.com/example/blockchain-js-sdk)
- Python: [blockchain-python-sdk](https://github.com/example/blockchain-python-sdk)
- Java: [blockchain-java-sdk](https://github.com/example/blockchain-java-sdk)

## API Changelog

### v1.2.0 (Current)
- Added webhook support
- Improved transaction validation error messages
- Added pagination to wallet transactions endpoint

### v1.1.0
- Added rate limiting
- Added authentication endpoints
- Improved error handling

### v1.0.0
- Initial release with basic blockchain operations 
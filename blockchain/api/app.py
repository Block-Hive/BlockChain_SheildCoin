from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import bleach
import re
from ..core.blockchain import Blockchain
from ..core.transaction import Transaction
from ..core.transaction_pool import TransactionPool
from ..crypto.wallet import Wallet
from ..network.dht_node import DHTNode
import threading
import argparse
import time
import socket
import os
import sys
import random
import requests
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Whitelist for allowed hosts
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Function to test TCP connectivity
def test_tcp_connectivity(host, port, timeout=3):
    """Test TCP connectivity to a host:port with timeout."""
    try:
        logger.info(f"Testing TCP connectivity to {host}:{port}")
        # Create a socket object
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        
        # Connect to the server
        s.connect((host, port))
        s.close()
        logger.info(f"Successfully connected to {host}:{port}")
        return True
    except Exception as e:
        logger.warning(f"Failed to connect to {host}:{port}: {e}")
        return False

# Track request rates for basic rate limiting
request_counts = {}

# Parse command line arguments
parser = argparse.ArgumentParser(description='Start a blockchain node')
parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to bind to')
parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
parser.add_argument('--dht-port', type=int, default=None, help='Port for DHT (defaults to port+1000)')
parser.add_argument('--bootstrap', type=str, help='Bootstrap node address (host:port)')
parser.add_argument('--local-ip', type=str, help='Explicitly set the local IP address to use for this node')
# Add secure options
parser.add_argument('--ssl-cert', type=str, help='Path to SSL certificate for HTTPS')
parser.add_argument('--ssl-key', type=str, help='Path to SSL key for HTTPS')
parser.add_argument('--allowed-hosts', type=str, help='Comma-separated list of allowed hosts')
args = parser.parse_args()

# If DHT port not specified, use port+1000
if args.dht_port is None:
    args.dht_port = args.port + 1000

# Add custom hosts to whitelist if provided
if args.allowed_hosts:
    ALLOWED_HOSTS.extend(args.allowed_hosts.split(','))

# Test firewall if bootstrap node is provided
if args.bootstrap:
    # Extract host and port from bootstrap
    if ':' in args.bootstrap:
        bootstrap_host, bootstrap_port = args.bootstrap.split(':')
    else:
        bootstrap_host = args.bootstrap
        bootstrap_port = args.dht_port
    
    # For 0.0.0.0, use 127.0.0.1
    if bootstrap_host == '0.0.0.0':
        bootstrap_host = '127.0.0.1'
    
    # Test TCP connectivity
    tcp_connectivity = test_tcp_connectivity(bootstrap_host, int(bootstrap_port))
    if not tcp_connectivity:
        logger.warning(f"Cannot connect to bootstrap node at {bootstrap_host}:{bootstrap_port}")
        logger.warning("This might be due to a firewall or the bootstrap node not running.")
        logger.warning("Continuing anyway, but node might not be able to join the network.")

# Create Flask app
app = Flask(__name__)

# Add CORS protection
CORS(app, resources={r"/*": {"origins": ALLOWED_HOSTS}})

# Add rate limiting - modified to handle different Flask-Limiter versions
try:
    # New version style
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["200 per day", "50 per hour", "5 per minute"]
    )
except TypeError:
    try:
        # Old version style
        limiter = Limiter(
            app,
            key_func=get_remote_address,
            default_limits=["200 per day", "50 per hour", "5 per minute"]
        )
    except Exception as e:
        logger.warning(f"Could not initialize rate limiter: {e}")
        # Fallback implementation without rate limiting
        class DummyLimiter:
            def limit(self, limit_value, key_func=None):
                def decorator(f):
                    return f
                return decorator
        limiter = DummyLimiter()

def get_local_ip():
    """Get the local IP address of this machine that can be reached from other machines."""
    try:
        # This connects to an external server but doesn't send any data
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        # Fallback methods if the above fails
        try:
            # Try using hostname resolution
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            if not ip.startswith('127.'):
                return ip
        except:
            pass
            
        try:
            # Try using netifaces library if available
            import netifaces
            for interface in netifaces.interfaces():
                addrs = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addrs:
                    for addr in addrs[netifaces.AF_INET]:
                        ip = addr['addr']
                        # Skip loopback addresses
                        if not ip.startswith('127.'):
                            return ip
        except ImportError:
            pass
            
        # Last resort fallback
        return '127.0.0.1'

# Get local IP address
if args.local_ip:
    # Use explicitly provided IP
    local_ip = args.local_ip
    print(f"Using provided local IP: {local_ip}")
elif args.host == '0.0.0.0':
    # Auto-detect IP
    local_ip = get_local_ip()
    print(f"Detected local IP: {local_ip}")
else:
    # Use the host as the local IP
    local_ip = args.host

# Initialize blockchain and transaction pool
blockchain = Blockchain()
transaction_pool = TransactionPool()

# Initialize DHT node
bootstrap_nodes = []
if args.bootstrap:
    # Try both loopback and external IPs when connecting to bootstrap
    if ':' in args.bootstrap:
        bootstrap_host, bootstrap_port = args.bootstrap.split(':')
        if bootstrap_host in ['0.0.0.0', '127.0.0.1', 'localhost']:
            # If bootstrap is on this machine, try with the actual node IP
            bootstrap_nodes = [f'{local_ip}:{bootstrap_port}']
        else:
            bootstrap_nodes = [args.bootstrap]
    else:
        # No port specified, use DHT port
        bootstrap_host = args.bootstrap
        if bootstrap_host in ['0.0.0.0', '127.0.0.1', 'localhost']:
            bootstrap_nodes = [f'{local_ip}:{args.dht_port}']
        else:
            bootstrap_nodes = [f'{bootstrap_host}:{args.dht_port}']
        
print(f"Initializing DHT node with bootstrap nodes: {bootstrap_nodes}")

# Try to initialize DHT node with retries and random ports if needed
dht_node = None
max_dht_retries = 5
for retry in range(max_dht_retries):
    try:
        dht_port = args.dht_port + retry
        print(f"Trying DHT port: {dht_port}")
        dht_node = DHTNode(
            host=local_ip,
            port=dht_port,
            bootstrap_nodes=bootstrap_nodes
        )
        print(f"Successfully initialized DHT node on port {dht_port}")
        break
    except Exception as e:
        print(f"Failed to initialize DHT node on port {dht_port}: {e}")
        if retry == max_dht_retries - 1:
            print("Failed to initialize DHT node after maximum retries. Exiting.")
            sys.exit(1)

# Set blockchain in DHT node
dht_node.blockchain = blockchain

# Start DHT node
dht_thread = threading.Thread(target=dht_node.start)
dht_thread.daemon = True
dht_thread.start()

# Initialize chain based on node type
if not bootstrap_nodes:
    print("This is a bootstrap node. Creating genesis block...")
    # Create genesis block with fixed seed for consistency
    blockchain._create_genesis_block(seed="fixed_seed_for_genesis")
    print(f"Genesis block created with hash: {blockchain.chain[0].hash}")
else:
    print("This is a joining node. Getting chain from bootstrap node...")
    # Try to get chain from bootstrap node
    max_retries = 5
    retry_delay = 2
    success = False
    
    for retry in range(max_retries):
        try:
            for node in bootstrap_nodes:
                host, port = node.split(':')
                print(f"Attempting to connect to bootstrap node {host}:{port} (attempt {retry + 1}/{max_retries})")
                
                # Try to get chain
                response = dht_node._send_message_with_response((host, int(port)), {
                    'type': 'get_chain'
                })
                
                if response and response.get('type') == 'chain_response':
                    chain_data = response.get('chain')
                    if chain_data:
                        blockchain.replace_chain(chain_data['chain'])
                        print(f"Successfully received chain from {host}:{port}")
                        print(f"Chain length: {len(blockchain.chain)}")
                        print(f"Genesis block hash: {blockchain.chain[0].hash}")
                        success = True
                        break
            
            if success:
                break
            
            print(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
        except Exception as e:
            print(f"Failed to connect (attempt {retry + 1}/{max_retries}): {e}")
            if retry < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)

    if not success:
        print("Failed to get chain from bootstrap node after maximum retries")
        print("Creating new chain since bootstrap connection failed")
        blockchain._create_genesis_block(seed="fixed_seed_for_genesis")
        print(f"Genesis block created with hash: {blockchain.chain[0].hash}")

@app.route('/chain', methods=['GET'])
@limiter.limit("10 per minute")
def get_chain():
    """Get the full blockchain."""
    return jsonify({
        'chain': blockchain.to_dict(),
        'length': len(blockchain.chain),
        'genesis_hash': blockchain.chain[0].hash if blockchain.chain else None
    }), 200

@app.route('/transactions/new', methods=['POST'])
@limiter.limit("20 per minute")
def new_transaction():
    """Create a new transaction."""
    try:
        # Validate JSON format
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400
            
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['sender', 'recipient', 'amount', 'signature']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
            
        # Validate input data
        if not is_valid_address(data['sender']):
            return jsonify({'error': 'Invalid sender address format'}), 400
            
        if not is_valid_address(data['recipient']):
            return jsonify({'error': 'Invalid recipient address format'}), 400
            
        if not is_valid_amount(data['amount']):
            return jsonify({'error': 'Invalid amount'}), 400
        
        transaction = Transaction(
            sender=data['sender'],
            recipient=data['recipient'],
            amount=float(data['amount']),
            signature=data['signature']
        )
        
        # Verify the transaction
        if not transaction.verify():
            return jsonify({'error': 'Transaction verification failed'}), 400
        
        # Add to transaction pool
        success = blockchain.add_transaction(transaction)
        
        if success:
            return jsonify({
                'message': 'Transaction added to pool',
                'transaction': transaction.to_dict()
            }), 201
        else:
            return jsonify({'error': 'Failed to add transaction'}), 400
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error processing transaction: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/mine', methods=['GET'])
@limiter.limit("5 per minute")
def mine():
    """Mine a new block with pending transactions."""
    try:
        # Get and validate miner address
        miner_address = request.args.get('address', 'system')
        if miner_address != 'system' and not is_valid_address(miner_address):
            return jsonify({'error': 'Invalid miner address'}), 400
            
        # Prevent resource exhaustion
        if request.args.get('debug'):
            return jsonify({'error': 'Debug parameter not allowed'}), 400
        
        # Apply mining throttling
        client_ip = request.remote_addr
        if client_ip in request_counts and request_counts[client_ip]['count'] > 5:
            logger.warning(f"Mining throttled for {client_ip}")
            return jsonify({'error': 'Mining requests throttled, try again later'}), 429
            
        # Mine a new block
        start_time = time.time()
        block = blockchain.mine_pending_transactions(miner_address)
        mining_time = time.time() - start_time
        
        if block:
            # Log mining activity
            logger.info(f"Block mined by {miner_address} in {mining_time:.2f}s")
            dht_node.broadcast_block(block)
            return jsonify({
                'message': 'New block mined',
                'block': block.to_dict(),
                'balance': blockchain.get_balance(miner_address)
            }), 200
        else:
            return jsonify({'message': 'No transactions to mine'}), 200
    except Exception as e:
        logger.error(f"Error mining block: {e}")
        return jsonify({'error': f'Error mining block: {str(e)}'}), 500

@app.route('/wallet/new', methods=['GET'])
def create_wallet():
    """Create a new wallet."""
    wallet = Wallet()
    return jsonify(wallet.to_dict()), 200

@app.route('/wallet/balance', methods=['GET'])
def get_balance():
    """Get wallet balance."""
    address = request.args.get('address')
    if not address:
        return jsonify({'error': 'Address required'}), 400
    
    balance = blockchain.get_balance(address)
    return jsonify({'balance': balance}), 200

@app.route('/peers', methods=['GET'])
def get_peers():
    """Get all connected peers."""
    peers = []
    for node_id, (host, port) in dht_node.routing_table.items():
        peers.append({
            'node_id': node_id,
            'host': host,
            'port': port
        })
    return jsonify({'peers': peers, 'count': len(peers)}), 200

@app.route('/', methods=['GET'])
def home():
    """Home endpoint."""
    return jsonify({
        'status': 'running',
        'node_id': dht_node.id,
        'host': dht_node.host,
        'port': dht_node.port,
        'dht_port': dht_node.port,
        'api_port': args.port,
        'peers_count': len(dht_node.routing_table),
        'chain_length': len(blockchain.chain)
    }), 200

@app.route('/node-info', methods=['GET'])
def node_info():
    """Get detailed node information."""
    return jsonify({
        'node_id': dht_node.id,
        'host': dht_node.host,
        'dht_port': dht_node.port,
        'api_port': args.port,
        'peers': [{'id': k, 'host': v[0], 'port': v[1]} for k, v in dht_node.routing_table.items()],
        'bootstrap_nodes': dht_node.bootstrap_nodes,
        'chain_length': len(blockchain.chain),
        'chain_hash': blockchain.chain[-1].hash if blockchain.chain else None,
        'transaction_count': len(blockchain.transaction_pool.transactions)
    }), 200

@app.route('/check-port/<host>/<int:port>', methods=['GET'])
def check_port(host, port):
    """Check if a port is open and reachable."""
    result = test_tcp_connectivity(host, port)
    return jsonify({
        'host': host,
        'port': port,
        'is_open': result
    }), 200

@app.route('/expose-ports', methods=['GET'])
def expose_ports():
    """Return information about this node's ports."""
    # Check if our own DHT port is open
    own_dht_open = test_tcp_connectivity('127.0.0.1', dht_node.port)
    return jsonify({
        'node_id': dht_node.id,
        'node_host': dht_node.host,
        'dht_port': dht_node.port,
        'api_port': args.port,
        'dht_port_open': own_dht_open,
        'network_interfaces': get_network_interfaces()
    }), 200

@app.route('/api/join', methods=['POST'])
def api_join():
    """API endpoint for nodes to join the network and get the blockchain."""
    try:
        data = request.get_json()
        node_id = data.get('node_id')
        host = data.get('host')
        port = data.get('port')
        
        if node_id and host and port:
            # Add node to routing table
            dht_node.routing_table[node_id] = (host, port)
            print(f"Node {node_id} joined from {host}:{port} via API")
            
            # Send blockchain
            return jsonify({
                'success': True,
                'chain': blockchain.to_dict(),
                'message': f"Welcome to the network, {node_id}!"
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': "Missing required fields: node_id, host, port"
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error processing join request: {str(e)}"
        }), 500

@app.route('/api/get-chain', methods=['GET'])
def api_get_chain():
    """API endpoint to get the blockchain."""
    try:
        return jsonify({
            'success': True,
            'chain': blockchain.to_dict()
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error retrieving chain: {str(e)}"
        }), 500

# Try to join network using HTTP API if bootstrap node is provided
if bootstrap_nodes:
    for attempt in range(5):
        try:
            for node in bootstrap_nodes:
                host, port = node.split(':')
                api_port = int(port) - 1000  # Convert DHT port to API port
                
                # First try direct DHT connection
                print(f"Attempting DHT connection to {host}:{port}")
                if test_tcp_connectivity(host, int(port)):
                    print(f"DHT port {port} is open on {host}")
                    
                    # Try to join using DHT protocol
                    response = dht_node._send_message_with_response(
                        (host, int(port)),
                        {'type': 'join', 'node_id': dht_node.id, 'host': dht_node.host, 'port': dht_node.port}
                    )
                    
                    if response and response.get('type') == 'join_ack':
                        print("Successfully joined using DHT protocol")
                        chain_data = response.get('chain')
                        if chain_data:
                            blockchain.replace_chain(chain_data['chain'])
                            print(f"Chain synchronized from {host}:{port}")
                            break
                
                # If DHT connection fails, try HTTP API
                print(f"Attempting HTTP connection to {host}:{api_port}")
                try:
                    # Try to join via API
                    join_response = requests.post(
                        f"http://{host}:{api_port}/api/join",
                        json={
                            'node_id': dht_node.id,
                            'host': dht_node.host,
                            'port': dht_node.port
                        },
                        timeout=5
                    )
                    
                    if join_response.status_code == 200:
                        print(f"Successfully joined via HTTP API")
                        data = join_response.json()
                        if data.get('success') and data.get('chain'):
                            blockchain.replace_chain(data['chain']['chain'])
                            print(f"Chain synchronized via HTTP API")
                            break
                except requests.RequestException as e:
                    print(f"HTTP API join failed: {e}")
                    
                    # Try to get chain directly via API
                    try:
                        chain_response = requests.get(f"http://{host}:{api_port}/api/get-chain", timeout=5)
                        if chain_response.status_code == 200:
                            data = chain_response.json()
                            if data.get('success') and data.get('chain'):
                                blockchain.replace_chain(data['chain']['chain'])
                                print(f"Chain synchronized via HTTP API")
                                break
                    except requests.RequestException:
                        print(f"HTTP API get-chain failed")
            
            else:  # No break
                print(f"Could not join network on attempt {attempt+1}/5. Retrying...")
                time.sleep(2)
                continue
            
            # If we got here, we successfully joined
            break
        
        except Exception as e:
            print(f"Error joining network: {e}")
            time.sleep(2)
    
    else:  # No break from for loop
        print("Failed to join network after multiple attempts.")
        print("Creating a new blockchain instead.")
        blockchain._create_genesis_block(seed="fixed_seed_for_genesis")
        print(f"Genesis block created with hash: {blockchain.chain[0].hash}")

def get_network_interfaces():
    """Get all network interfaces with their IP addresses."""
    interfaces = {}
    try:
        import netifaces
        for interface in netifaces.interfaces():
            addrs = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in addrs:
                interfaces[interface] = [addr['addr'] for addr in addrs[netifaces.AF_INET]]
    except ImportError:
        # Fallback if netifaces is not installed
        import subprocess
        output = subprocess.check_output(['ip', 'addr']).decode()
        interfaces = {'output': output}
    return interfaces

if __name__ == '__main__':
    try:
        print(f"Starting Flask app on {args.host}:{args.port}")
        app.run(
            host=args.host,
            port=args.port,
            debug=True,
            use_reloader=False  # Disable Flask's reloader to prevent double initialization
        )
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1) 
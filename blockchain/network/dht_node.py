import socket
import threading
import json
import hashlib
import time
import selectors
from typing import Dict, Tuple, List, Optional

class DHTNode:
    def __init__(self, host: str, port: int, bootstrap_nodes: List[str] = None):
        self.host = host
        self.port = port
        self.id = self._generate_node_id()
        self.routing_table = {}  # node_id -> (host, port)
        self.bootstrap_nodes = bootstrap_nodes or []
        self.running = False
        self.response_handlers = {}  # message_id -> (event, response)
        
        try:
            # Create TCP socket with proper options
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Try to set SO_REUSEPORT if available
            try:
                self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            except AttributeError:
                # SO_REUSEPORT might not be available on all systems
                pass
            
            # Ensure we're binding to all interfaces to accept connections from anywhere
            bind_host = '0.0.0.0'  # Bind to all interfaces, regardless of specified host
            self.server_socket.bind((bind_host, port))
            self.server_socket.listen(10)  # Increased backlog for more connections
            
            print(f"Node initialized with ID: {self.id} on {host}:{port} (bound to all interfaces)")
        except Exception as e:
            print(f"Error initializing DHT node: {e}")
            raise

    def _generate_node_id(self) -> str:
        """Generate a unique node ID."""
        return hashlib.sha256(f"{self.host}:{self.port}:{time.time()}".encode()).hexdigest()[:16]

    def start(self):
        """Start the DHT node."""
        self.running = True
        print(f"Starting DHT node {self.id}")
        
        # Start listening thread
        listen_thread = threading.Thread(target=self._listen, daemon=True)
        listen_thread.start()
        print(f"DHT node listening thread started on {self.host}:{self.port}")
        
        # Wait a bit for server to start properly
        time.sleep(1)
        
        # Connect to bootstrap nodes if any
        if self.bootstrap_nodes:
            self._bootstrap()

    def _listen(self):
        """Listen for incoming connections using simple TCP."""
        print(f"DHT node listening for connections on {self.host}:{self.port}")
        
        while self.running:
            try:
                # Accept connection (blocking call)
                client_socket, addr = self.server_socket.accept()
                print(f"Accepted connection from {addr}")
                
                # Handle connection in a new thread to avoid blocking
                client_thread = threading.Thread(
                    target=self._handle_client_connection,
                    args=(client_socket, addr),
                    daemon=True
                )
                client_thread.start()
            except Exception as e:
                if self.running:  # Only print error if node is still running
                    print(f"Error accepting connection: {e}")

    def _handle_client_connection(self, client_socket, addr):
        """Handle a client connection."""
        try:
            # Receive data
            data = client_socket.recv(65536)
            if data:
                try:
                    message = json.loads(data.decode())
                    print(f"Received message from {addr}: {message.get('type')}")
                    
                    # Process message and send response
                    response = self._handle_message(message, addr)
                    if response:
                        print(f"Sending response to {addr}: {response.get('type')}")
                        client_socket.sendall(json.dumps(response).encode())
                    else:
                        print(f"No response for message from {addr}")
                        # Send an ack if there's no specific response
                        client_socket.sendall(json.dumps({'type': 'ack'}).encode())
                except json.JSONDecodeError as e:
                    print(f"Error decoding message from {addr}: {e}")
                    client_socket.sendall(json.dumps({'type': 'error', 'error': 'Invalid JSON'}).encode())
            else:
                print(f"Empty data received from {addr}")
        except Exception as e:
            print(f"Error handling client connection: {e}")
        finally:
            try:
                client_socket.close()
            except:
                pass

    def _send_message_with_response(self, addr: Tuple[str, int], message: dict, timeout: int = 5) -> Optional[dict]:
        """
        Send a message and wait for a response.
        
        Args:
            addr: Address to send message to
            message: Message to send
            timeout: Timeout in seconds
            
        Returns:
            Response message if received, None otherwise
        """
        try:
            print(f"Sending message to {addr}: {message.get('type')}")
            # Create a client socket
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(timeout)
            
            # Connect to the server
            print(f"Connecting to {addr}")
            client_socket.connect(addr)
            print(f"Connected to {addr}")
            
            # Send message
            message_data = json.dumps(message).encode()
            client_socket.sendall(message_data)
            print(f"Sent {len(message_data)} bytes to {addr}")
            
            # Receive response
            data = client_socket.recv(65536)
            print(f"Received {len(data)} bytes from {addr}")
            
            if data:
                response = json.loads(data.decode())
                print(f"Received response from {addr}: {response.get('type')}")
                
                # Close socket
                client_socket.close()
                
                return response
            else:
                print(f"Empty response from {addr}")
                return None
        except (socket.timeout, ConnectionRefusedError) as e:
            print(f"Connection error while sending to {addr}: {e}")
            return None
        except Exception as e:
            print(f"Error sending message: {e}")
            return None

    def _handle_message(self, message: dict, addr: Tuple[str, int]):
        """Handle incoming messages."""
        try:
            msg_type = message.get('type')
            
            print(f"Handling message type: {msg_type} from {addr}")
            
            if msg_type == 'join':
                return self._handle_join(message, addr)
            elif msg_type == 'get_chain':
                return self._handle_get_chain(message, addr)
            elif msg_type == 'new_block':
                self._handle_new_block(message)
                return {'type': 'ack'}
            elif msg_type == 'new_transaction':
                self._handle_new_transaction(message)
                return {'type': 'ack'}
            else:
                print(f"Unknown message type: {msg_type}")
                return {'type': 'error', 'error': 'Unknown message type'}
        except Exception as e:
            print(f"Error handling message: {e}")
            return {'type': 'error', 'error': str(e)}

    def _handle_join(self, message: dict, addr: Tuple[str, int]):
        """Handle a node joining the network."""
        try:
            node_id = message.get('node_id')
            host = message.get('host')
            port = message.get('port')
            
            if node_id and host and port:
                self.routing_table[node_id] = (host, port)
                print(f"Node {node_id} joined from {host}:{port}")
                
                # Send acknowledgment with chain
                if hasattr(self, 'blockchain'):
                    return {
                        'type': 'join_ack',
                        'chain': self.blockchain.to_dict()
                    }
                else:
                    return {'type': 'join_ack', 'error': 'No blockchain available'}
            return {'type': 'error', 'error': 'Invalid join request'}
        except Exception as e:
            print(f"Error handling join: {e}")
            return {'type': 'error', 'error': str(e)}

    def _handle_get_chain(self, message: dict, addr: Tuple[str, int]):
        """Handle chain request."""
        try:
            if hasattr(self, 'blockchain'):
                print(f"Sending chain to {addr[0]}:{addr[1]}")
                return {
                    'type': 'chain_response',
                    'chain': self.blockchain.to_dict()
                }
            else:
                return {'type': 'error', 'error': 'No blockchain available'}
        except Exception as e:
            print(f"Error handling get_chain: {e}")
            return {'type': 'error', 'error': str(e)}

    def _handle_new_block(self, message: dict):
        """Handle new block broadcast."""
        try:
            if hasattr(self, 'blockchain'):
                block = message.get('block')
                if block:
                    self.blockchain.add_block_from_dict(block)
                    print(f"Added new block: {block.get('hash', 'unknown')}")
        except Exception as e:
            print(f"Error handling new block: {e}")

    def _handle_new_transaction(self, message: dict):
        """Handle new transaction broadcast."""
        try:
            if hasattr(self, 'blockchain'):
                transaction = message.get('transaction')
                if transaction:
                    self.blockchain.add_transaction_from_dict(transaction)
                    print(f"Added new transaction: {transaction.get('hash', 'unknown')}")
        except Exception as e:
            print(f"Error handling new transaction: {e}")

    def _bootstrap(self):
        """Connect to bootstrap nodes."""
        print("Connecting to bootstrap nodes...")
        for node in self.bootstrap_nodes:
            try:
                host, port = node.split(':')
                print(f"Connecting to bootstrap node: {host}:{port}")
                
                # Send join request
                message = {
                    'type': 'join',
                    'node_id': self.id,
                    'host': self.host,
                    'port': self.port
                }
                
                # Try to get chain with response
                response = self._send_message_with_response((host, int(port)), message)
                
                if response and response.get('type') == 'join_ack':
                    chain_data = response.get('chain')
                    if chain_data and hasattr(self, 'blockchain'):
                        self.blockchain.replace_chain(chain_data['chain'])
                        print(f"Successfully synchronized chain from {host}:{port}")
                        print(f"Chain length: {len(self.blockchain.chain)}")
                        print(f"Genesis block hash: {self.blockchain.chain[0].hash}")
                        return True
                
                # If join failed, try direct chain request
                message = {'type': 'get_chain'}
                response = self._send_message_with_response((host, int(port)), message)
                
                if response and response.get('type') == 'chain_response':
                    chain_data = response.get('chain')
                    if chain_data and hasattr(self, 'blockchain'):
                        self.blockchain.replace_chain(chain_data['chain'])
                        print(f"Successfully synchronized chain from {host}:{port}")
                        print(f"Chain length: {len(self.blockchain.chain)}")
                        print(f"Genesis block hash: {self.blockchain.chain[0].hash}")
                        return True
                
            except Exception as e:
                print(f"Failed to connect to {node}: {e}")
        return False

    def broadcast_block(self, block):
        """Broadcast a new block to all nodes."""
        message = {
            'type': 'new_block',
            'block': block.to_dict()
        }
        
        success_count = 0
        for node_id, (host, port) in list(self.routing_table.items()):
            if node_id != self.id:
                try:
                    print(f"Broadcasting new block to {host}:{port}")
                    response = self._send_message_with_response((host, port), message)
                    if response and response.get('type') == 'ack':
                        success_count += 1
                    else:
                        print(f"Failed to get acknowledgment from {host}:{port}")
                except Exception as e:
                    print(f"Error broadcasting block to {host}:{port}: {e}")
                    # Remove failed node from routing table
                    self.routing_table.pop(node_id, None)
        
        print(f"Block broadcast complete. Reached {success_count}/{len(self.routing_table)} nodes.")
        return success_count

    def broadcast_transaction(self, transaction):
        """Broadcast a new transaction to all nodes."""
        message = {
            'type': 'new_transaction',
            'transaction': transaction.to_dict()
        }
        
        success_count = 0
        for node_id, (host, port) in list(self.routing_table.items()):
            if node_id != self.id:
                try:
                    print(f"Broadcasting new transaction to {host}:{port}")
                    response = self._send_message_with_response((host, port), message)
                    if response and response.get('type') == 'ack':
                        success_count += 1
                    else:
                        print(f"Failed to get acknowledgment from {host}:{port}")
                except Exception as e:
                    print(f"Error broadcasting transaction to {host}:{port}: {e}")
                    # Remove failed node from routing table
                    self.routing_table.pop(node_id, None)
        
        print(f"Transaction broadcast complete. Reached {success_count}/{len(self.routing_table)} nodes.")
        return success_count

    def stop(self):
        """Stop the DHT node."""
        self.running = False
        self.server_socket.close() 
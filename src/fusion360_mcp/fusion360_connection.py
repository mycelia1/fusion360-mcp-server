"""
Fusion360 Connection Handler

Manages socket connection between the MCP server and Fusion360 add-in.
Based on the BlenderMCP connection architecture.
"""

import socket
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Fusion360MCPConnection")

@dataclass
class Fusion360Connection:
    """Manages connection to the Fusion360 add-in socket server"""
    host: str
    port: int
    sock: socket.socket = None
    
    def connect(self) -> bool:
        """Connect to the Fusion360 add-in socket server"""
        if self.sock:
            return True
            
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            logger.info(f"Connected to Fusion360 at {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Fusion360: {str(e)}")
            self.sock = None
            return False
    
    def disconnect(self):
        """Disconnect from the Fusion360 add-in"""
        if self.sock:
            try:
                self.sock.close()
            except Exception as e:
                logger.error(f"Error disconnecting from Fusion360: {str(e)}")
            finally:
                self.sock = None

    def receive_full_response(self, sock, buffer_size=8192):
        """Receive the complete response, potentially in multiple chunks"""
        chunks = []
        sock.settimeout(15.0)  # Timeout for response
        
        try:
            while True:
                try:
                    chunk = sock.recv(buffer_size)
                    if not chunk:
                        if not chunks:
                            raise Exception("Connection closed before receiving any data")
                        break
                    
                    chunks.append(chunk)
                    
                    # Check if we've received a complete JSON object
                    try:
                        data = b''.join(chunks)
                        json.loads(data.decode('utf-8'))
                        logger.info(f"Received complete response ({len(data)} bytes)")
                        return data
                    except json.JSONDecodeError:
                        # Incomplete JSON, continue receiving
                        continue
                        
                except socket.timeout:
                    logger.warning("Socket timeout during chunked receive")
                    break
                except (ConnectionError, BrokenPipeError, ConnectionResetError) as e:
                    logger.error(f"Socket connection error during receive: {str(e)}")
                    raise
                    
        except socket.timeout:
            logger.warning("Socket timeout during chunked receive")
        except Exception as e:
            logger.error(f"Error during receive: {str(e)}")
            raise
            
        # Try to use what we have
        if chunks:
            data = b''.join(chunks)
            logger.info(f"Returning data after receive completion ({len(data)} bytes)")
            try:
                json.loads(data.decode('utf-8'))
                return data
            except json.JSONDecodeError:
                raise Exception("Incomplete JSON response received")
        else:
            raise Exception("No data received")

    def send_command(self, command_type: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send a command to Fusion360 and return the response"""
        if not self.sock and not self.connect():
            raise ConnectionError("Not connected to Fusion360")
        
        command = {
            "type": command_type,
            "params": params or {}
        }
        
        try:
            logger.info(f"Sending command: {command_type} with params: {params}")
            
            # Send the command
            self.sock.sendall(json.dumps(command).encode('utf-8'))
            logger.info("Command sent, waiting for response...")
            
            # Set timeout for receiving
            self.sock.settimeout(15.0)
            
            # Receive the response
            response_data = self.receive_full_response(self.sock)
            logger.info(f"Received {len(response_data)} bytes of data")
            
            response = json.loads(response_data.decode('utf-8'))
            logger.info(f"Response parsed, status: {response.get('status', 'unknown')}")
            
            if response.get("status") == "error":
                logger.error(f"Fusion360 error: {response.get('message')}")
                raise Exception(response.get("message", "Unknown error from Fusion360"))
            
            return response.get("result", {})
            
        except socket.timeout:
            logger.error("Socket timeout while waiting for response from Fusion360")
            self.sock = None
            raise Exception("Timeout waiting for Fusion360 response - try simplifying your request")
        except (ConnectionError, BrokenPipeError, ConnectionResetError) as e:
            logger.error(f"Socket connection error: {str(e)}")
            self.sock = None
            raise Exception(f"Connection to Fusion360 lost: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from Fusion360: {str(e)}")
            if 'response_data' in locals() and response_data:
                logger.error(f"Raw response (first 200 bytes): {response_data[:200]}")
            raise Exception(f"Invalid response from Fusion360: {str(e)}")
        except Exception as e:
            logger.error(f"Error communicating with Fusion360: {str(e)}")
            self.sock = None
            raise Exception(f"Communication error with Fusion360: {str(e)}")


# Global connection for the MCP server
_fusion360_connection = None

def get_fusion360_connection() -> Optional[Fusion360Connection]:
    """Get or create a persistent Fusion360 connection"""
    global _fusion360_connection
    
    # If we have an existing connection, check if it's still valid
    if _fusion360_connection is not None:
        try:
            # Test the connection with a ping command
            result = _fusion360_connection.send_command("get_scene_info")
            return _fusion360_connection
        except Exception as e:
            logger.warning(f"Existing connection is no longer valid: {str(e)}")
            try:
                _fusion360_connection.disconnect()
            except:
                pass
            _fusion360_connection = None
    
    # Create a new connection if needed
    if _fusion360_connection is None:
        _fusion360_connection = Fusion360Connection(host="localhost", port=9876)
        if not _fusion360_connection.connect():
            logger.warning("Failed to connect to Fusion360 - waiting for Fusion360 to become available")
            _fusion360_connection = None
            return None
        logger.info("Created new persistent connection to Fusion360")
    
    return _fusion360_connection

def check_fusion360_available() -> Optional[str]:
    """Helper function to check if Fusion360 is available and return error message if not"""
    fusion360 = get_fusion360_connection()
    if fusion360 is None:
        return "Fusion360 is not currently running or the MCP add-in is not started. Please start Fusion360 and enable the Fusion360MCP add-in."
    return None 
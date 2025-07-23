"""
Fusion360 MCP Socket Server

This runs inside Fusion360 and listens for commands from the MCP server.
Based on the BlenderMCP socket server architecture.
"""

import adsk.core
import adsk.fusion
import adsk.cam
import socket
import threading
import json
import time
import traceback
from .command_handler import CommandHandler

class Fusion360MCPServer:
    """Socket server that runs inside Fusion360 to receive MCP commands"""
    
    def __init__(self, host='localhost', port=9876):
        self.host = host
        self.port = port
        self.running = False
        self.socket = None
        self.server_thread = None
        self.command_handler = CommandHandler()
        
        # Get Fusion360 app and UI references
        self.app = adsk.core.Application.get()
        self.ui = self.app.userInterface
        
    def start(self):
        """Start the socket server"""
        if self.running:
            return False
            
        self.running = True
        
        try:
            # Create socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(1)
            
            # Start server thread
            self.server_thread = threading.Thread(target=self._server_loop)
            self.server_thread.daemon = True
            self.server_thread.start()
            
            return True
            
        except Exception as e:
            self.ui.messageBox(f"❌ Failed to start server: {str(e)}")
            self.stop()
            return False
            
    def stop(self):
        """Stop the socket server"""
        self.running = False
        
        # Close socket
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        
        # Wait for thread to finish
        if self.server_thread:
            try:
                if self.server_thread.is_alive():
                    self.server_thread.join(timeout=1.0)
            except:
                pass
            self.server_thread = None
        
        print("Fusion360MCP server stopped")
    
    def _server_loop(self):
        """Main server loop in a separate thread"""
        print("Fusion360MCP server thread started")
        self.socket.settimeout(1.0)  # Timeout to allow for stopping
        
        while self.running:
            try:
                # Accept new connection
                try:
                    client, address = self.socket.accept()
                    print(f"Connected to MCP client: {address}")
                    
                    # Handle client in a separate thread
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client,)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except socket.timeout:
                    # Just check running condition
                    continue
                except Exception as e:
                    print(f"Error accepting connection: {str(e)}")
                    time.sleep(0.5)
                    
            except Exception as e:
                print(f"Error in server loop: {str(e)}")
                if not self.running:
                    break
                time.sleep(0.5)
        
        print("Fusion360MCP server thread stopped")
    
    def _handle_client(self, client):
        """Handle connected MCP client"""
        print("MCP client handler started")
        client.settimeout(None)  # No timeout
        buffer = b''
        
        try:
            while self.running:
                # Receive data
                try:
                    data = client.recv(8192)
                    if not data:
                        print("MCP client disconnected")
                        break
                    
                    buffer += data
                    try:
                        # Try to parse command
                        command = json.loads(buffer.decode('utf-8'))
                        buffer = b''
                        
                        # Execute command - schedule execution in main thread
                        def execute_wrapper():
                            try:
                                response = self.command_handler.execute_command(command)
                                response_json = json.dumps(response)
                                try:
                                    client.sendall(response_json.encode('utf-8'))
                                except:
                                    print("Failed to send response - MCP client disconnected")
                            except Exception as e:
                                print(f"Error executing command: {str(e)}")
                                traceback.print_exc()
                                try:
                                    error_response = {
                                        "status": "error",
                                        "message": str(e)
                                    }
                                    client.sendall(json.dumps(error_response).encode('utf-8'))
                                except:
                                    pass
                            return None
                        
                        # Schedule execution in main thread using Fusion360's threading
                        # Note: Fusion360 doesn't have bpy.app.timers like Blender, 
                        # so we'll execute immediately but carefully
                        execute_wrapper()
                        
                    except json.JSONDecodeError:
                        # Incomplete data, wait for more
                        pass
                        
                except Exception as e:
                    print(f"Error receiving data: {str(e)}")
                    break
                    
        except Exception as e:
            print(f"Error in client handler: {str(e)}")
        finally:
            try:
                client.close()
            except:
                pass
            print("MCP client handler stopped")
    
    def is_running(self):
        """Check if server is running"""
        return self.running
    
    def get_status(self):
        """Get server status information"""
        return {
            "running": self.running,
            "host": self.host,
            "port": self.port,
            "has_thread": self.server_thread is not None and self.server_thread.is_alive()
        } 
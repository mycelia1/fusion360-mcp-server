"""
Fusion360MCP Add-in
Connect Fusion360 to Claude AI via Model Context Protocol

Based on the BlenderMCP architecture for direct execution in CAD software.
"""

import adsk.core
import adsk.fusion
import adsk.cam
import traceback
import threading
import socket
import json
import time
from .server.socket_server import Fusion360MCPServer
from .server.ui_panel import create_ui_panel, cleanup_ui

# Global variables
_app = None
_ui = None
_handlers = []
_mcp_server = None
_command_def = None

def run(context):
    """Entry point for the add-in"""
    global _app, _ui, _mcp_server
    
    try:
        _app = adsk.core.Application.get()
        _ui = _app.userInterface
        
        # Create the MCP server instance
        _mcp_server = Fusion360MCPServer(host='localhost', port=9876)
        
        # Create UI panel
        create_ui_panel(_ui, _mcp_server)
        
        _ui.messageBox('Fusion360MCP add-in loaded successfully!\n\nUse the "Fusion360MCP" panel to start the server.')
        
    except Exception as e:
        if _ui:
            _ui.messageBox(f'Failed to load Fusion360MCP add-in:\n{str(e)}\n\n{traceback.format_exc()}')

def stop(context):
    """Cleanup when add-in is stopped"""
    global _app, _ui, _mcp_server
    
    try:
        # Stop the server if running
        if _mcp_server:
            _mcp_server.stop()
            _mcp_server = None
        
        # Clean up UI
        cleanup_ui()
        
        # Clean up handlers
        for handler in _handlers:
            if handler:
                handler.deleteMe()
        _handlers.clear()
        
    except Exception as e:
        if _ui:
            _ui.messageBox(f'Error during cleanup:\n{str(e)}') 
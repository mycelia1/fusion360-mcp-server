"""
Fusion360MCP UI Panel

Creates a simple control panel in Fusion360's interface for managing the MCP server.
Similar to the Blender MCP sidebar panel.
"""

import adsk.core
import adsk.fusion
import traceback

# Global variables for UI cleanup
_workspace = None
_panel = None
_start_button_def = None
_stop_button_def = None
_status_text_def = None
_handlers = []

def create_ui_panel(ui, mcp_server):
    """Create the Fusion360MCP control panel"""
    global _workspace, _panel, _start_button_def, _stop_button_def, _status_text_def, _handlers
    
    try:
        # Get the workspace
        _workspace = ui.workspaces.itemById('FusionSolidEnvironment')
        if not _workspace:
            ui.messageBox('Could not find the Design workspace')
            return
        
        # Create a new panel
        _panel = _workspace.toolbarPanels.add('Fusion360MCP', 'Fusion360MCP')
        
        # Create Start Server button
        _start_button_def = ui.commandDefinitions.addButtonDefinition(
            'StartMCPServer',
            'Start MCP Server',
            'Start the Fusion360MCP server to connect with Claude/Cursor',
            ''
        )
        
        # Create Stop Server button
        _stop_button_def = ui.commandDefinitions.addButtonDefinition(
            'StopMCPServer',
            'Stop MCP Server', 
            'Stop the Fusion360MCP server',
            ''
        )
        
        # Add buttons to panel
        start_control = _panel.controls.addCommand(_start_button_def)
        stop_control = _panel.controls.addCommand(_stop_button_def)
        
        # Create command handlers
        start_handler = StartServerCommandHandler(mcp_server)
        _start_button_def.commandCreated.add(start_handler)
        _handlers.append(start_handler)
        
        stop_handler = StopServerCommandHandler(mcp_server)
        _stop_button_def.commandCreated.add(stop_handler)
        _handlers.append(stop_handler)
        
        # Add separator
        _panel.controls.addSeparator()
        
        ui.messageBox('✅ Fusion360MCP panel created successfully!\n\nLook for the "Fusion360MCP" panel in the toolbar.')
        
    except Exception as e:
        ui.messageBox(f'❌ Failed to create UI panel: {str(e)}\n\n{traceback.format_exc()}')

def cleanup_ui():
    """Clean up the UI panel and controls"""
    global _workspace, _panel, _start_button_def, _stop_button_def, _status_text_def, _handlers
    
    try:
        # Clean up handlers
        for handler in _handlers:
            if handler:
                try:
                    handler.deleteMe()
                except:
                    pass
        _handlers.clear()
        
        # Remove panel
        if _panel:
            try:
                _panel.deleteMe()
            except:
                pass
            _panel = None
        
        # Remove command definitions
        if _start_button_def:
            try:
                _start_button_def.deleteMe()
            except:
                pass
            _start_button_def = None
            
        if _stop_button_def:
            try:
                _stop_button_def.deleteMe()
            except:
                pass
            _stop_button_def = None
            
        _workspace = None
        
    except Exception as e:
        print(f'Error during UI cleanup: {str(e)}')

class StartServerCommandHandler(adsk.core.CommandCreatedEventHandler):
    """Handler for the Start Server command"""
    
    def __init__(self, mcp_server):
        super().__init__()
        self.mcp_server = mcp_server
        
    def notify(self, args):
        ui = adsk.core.Application.get().userInterface
        try:
            if self.mcp_server.is_running():
                ui.messageBox('MCP Server is already running!')
                return
            
            success = self.mcp_server.start()
            
            if success:
                ui.messageBox('✅ MCP Server started successfully!')
            else:
                ui.messageBox('❌ Failed to start MCP Server')
            
        except Exception as e:
                        ui.messageBox(f'❌ Error starting server: {str(e)}')


class StopServerCommandHandler(adsk.core.CommandCreatedEventHandler):
    """Handler for the Stop Server command"""
    
    def __init__(self, mcp_server):
        super().__init__()
        self.mcp_server = mcp_server
        
    def notify(self, args):
        ui = adsk.core.Application.get().userInterface
        try:
            if not self.mcp_server.is_running():
                ui.messageBox('MCP Server is not running!')
                return
                
            self.mcp_server.stop()
            ui.messageBox('✅ MCP Server stopped successfully!')
            
        except Exception as e:
            ui.messageBox(f'❌ Error stopping server: {str(e)}') 
"""Fusion360 MCP Server - Main server implementation with socket connection support."""

import anyio
import click
import json
import mcp.types as types
from mcp.server.lowlevel import Server
from typing import List

from .tools import get_tool_list, get_tool_by_name
from .script_generator import generate_single_tool_script, generate_multi_tool_script
from .fusion360_connection import get_fusion360_connection, check_fusion360_available


@click.command()
@click.option("--port", default=8000, help="Port to listen on for SSE")
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse"]),
    default="stdio",
    help="Transport type",
)
@click.option(
    "--mode",
    type=click.Choice(["socket", "script"]),
    default="socket",
    help="Execution mode: socket for direct execution, script for script generation",
)
def main(port: int, transport: str, mode: str) -> int:
    """Main entry point for the Fusion360 MCP Server."""
    
    app = Server("fusion360-mcp-server")

    @app.list_tools()
    async def list_tools() -> List[types.Tool]:
        """List all available Fusion360 tools."""
        return get_tool_list()

    @app.call_tool()
    async def call_tool(name: str, arguments: dict) -> List[types.ContentBlock]:
        """Handle tool calls - either direct execution or script generation."""
        
        # Validate tool exists
        tool_def = get_tool_by_name(name)
        if not tool_def:
            raise ValueError(f"Unknown tool: {name}")
        
        if mode == "socket":
            # Direct execution mode
            return await execute_tool_directly(name, arguments)
        else:
            # Script generation mode (fallback)
            return await generate_tool_script(name, arguments)

    async def execute_tool_directly(name: str, arguments: dict) -> List[types.ContentBlock]:
        """Execute tool directly in Fusion360 via socket connection."""
        try:
            # Check if Fusion360 is available
            error_msg = check_fusion360_available()
            if error_msg:
                return [types.TextContent(type="text", text=error_msg)]
            
            # Get connection and send command
            fusion360 = get_fusion360_connection()
            result = fusion360.send_command(name, arguments)
            
            # Format the response
            response_text = f"✅ **{name}** executed successfully in Fusion360!\n\n"
            
            if isinstance(result, dict):
                # Pretty format the result
                for key, value in result.items():
                    if key == "success" and value:
                        continue
                    response_text += f"**{key.title()}**: {value}\n"
            else:
                response_text += f"Result: {result}"
            
            return [types.TextContent(type="text", text=response_text)]
            
        except Exception as e:
            error_text = f"❌ **Error executing {name}**: {str(e)}\n\n"
            error_text += "💡 **Troubleshooting:**\n"
            error_text += "- Make sure Fusion360 is running\n"
            error_text += "- Enable the Fusion360MCP add-in\n"
            error_text += "- Click 'Start MCP Server' in the Fusion360MCP panel\n"
            error_text += "- Ensure you have an active design document"
            
            return [types.TextContent(type="text", text=error_text)]

    async def generate_tool_script(name: str, arguments: dict) -> List[types.ContentBlock]:
        """Generate Fusion360 script (fallback mode)."""
        try:
            script = generate_single_tool_script(name, arguments)
            
            return [
                types.TextContent(
                    type="text",
                    text=f"Generated Fusion360 script for '{name}':\n\n```python\n{script}\n```"
                )
            ]
            
        except Exception as e:
            error_message = f"Error generating script for '{name}': {str(e)}"
            return [types.TextContent(type="text", text=error_message)]

    @app.list_resources()
    async def list_resources() -> List[types.Resource]:
        """List available resources."""
        return [
            types.Resource(
                uri="fusion360://status",
                name="Fusion360 Connection Status",
                description="Current status of the connection to Fusion360",
                mimeType="application/json"
            ),
            types.Resource(
                uri="fusion360://tools",
                name="Fusion360 Tools Registry",
                description="Complete registry of available Fusion360 tools and their parameters",
                mimeType="application/json"
            ),
            types.Resource(
                uri="fusion360://examples",
                name="Script Examples", 
                description="Example scripts showing how to use Fusion360 tools",
                mimeType="text/plain"
            ),
            types.Resource(
                uri="fusion360://help",
                name="Setup Instructions",
                description="Instructions for setting up the Fusion360MCP add-in",
                mimeType="text/plain"
            )
        ]

    @app.read_resource()
    async def read_resource(uri: str) -> str:
        """Read resource content."""
        if uri == "fusion360://status":
            # Check connection status
            try:
                fusion360 = get_fusion360_connection()
                if fusion360:
                    # Try to get scene info to verify connection
                    scene_info = fusion360.send_command("get_scene_info")
                    status = {
                        "connected": True,
                        "mode": mode,
                        "fusion360_design": scene_info.get("design_name", "Unknown"),
                        "scene_info": scene_info
                    }
                else:
                    status = {
                        "connected": False,
                        "mode": mode,
                        "error": "Cannot connect to Fusion360. Make sure Fusion360 is running and the MCP add-in is enabled."
                    }
            except Exception as e:
                status = {
                    "connected": False,
                    "mode": mode,
                    "error": str(e)
                }
            
            return json.dumps(status, indent=2)
        
        elif uri == "fusion360://tools":
            # Return the complete tool registry as JSON
            tools_data = {
                "mode": mode,
                "tools": [
                    {
                        "name": tool.name,
                        "title": tool.title,
                        "description": tool.description,
                        "inputSchema": tool.inputSchema
                    }
                    for tool in get_tool_list()
                ]
            }
            return json.dumps(tools_data, indent=2)
        
        elif uri == "fusion360://examples":
            return f"""# Fusion360 MCP Server Examples (Mode: {mode})

## Basic Rectangle and Extrude
1. create_sketch(plane="xy")
2. draw_rectangle(width=20, height=10)
3. extrude(height=5)

## Circle with Fillet
1. create_sketch(plane="xy") 
2. draw_circle(radius=15)
3. extrude(height=8)
4. fillet(radius=2, edge_selection="top")

## Complex Shape with Mirror
1. create_sketch(plane="xy")
2. draw_rectangle(width=30, height=20)
3. extrude(height=10)
4. chamfer(distance=3, edge_selection="top")
5. shell(thickness=2, face_selection="top")
6. mirror(mirror_plane="yz")

## Revolve Example
1. create_sketch(plane="xz")
2. draw_rectangle(width=5, height=20, origin_x=10)
3. revolve(angle=360, axis_origin_x=0, axis_direction_x=1)

{'Direct execution in Fusion360 via socket connection.' if mode == 'socket' else 'Each tool generates Fusion360 Python API code that can be executed as a script in Fusion360.'}
"""
        
        elif uri == "fusion360://help":
            return """# Fusion360MCP Setup Instructions

## 🎯 Two Modes Available

### 🚀 Socket Mode (Recommended)
Direct execution in Fusion360 - no copy/paste needed!

**Setup:**
1. Install the Fusion360MCP add-in in Fusion360
2. Start the MCP server in socket mode (default)
3. Enjoy direct execution!

### 📜 Script Mode (Fallback)  
Generates scripts for manual execution.

**Setup:**
1. Start MCP server with --mode script
2. Copy generated scripts to Fusion360
3. Run scripts manually

## 📥 Installing the Fusion360MCP Add-in

1. **Copy add-in files** to:
   ```
   C:\\Users\\Will\\AppData\\Roaming\\Autodesk\\Autodesk Fusion 360\\API\\AddIns\\Fusion360MCP\\
   ```

2. **Enable in Fusion360:**
   - Utilities → ADD-INS → Scripts and Add-Ins
   - Add-Ins tab → Find "Fusion360MCP" 
   - Check the box → Click "Run"

3. **Start the server:**
   - Look for "Fusion360MCP" panel in toolbar
   - Click "Start MCP Server"
   - Confirm: "server started on localhost:9876"

## 🔧 Usage

Once set up, you can use tools directly:
- create_sketch(plane="xy")
- draw_rectangle(width=50, height=30)
- extrude(height=15)

Commands execute immediately in Fusion360!

## 🐛 Troubleshooting

**"Cannot connect to Fusion360":**
- Make sure Fusion360 is running
- Enable the Fusion360MCP add-in  
- Click "Start MCP Server" in the add-in panel
- Check port 9876 is not blocked

**Commands not working:**
- Ensure you have an active design document
- Check the Fusion360 console for errors
- Try restarting both the add-in and MCP server
"""
        
        else:
            raise ValueError(f"Unknown resource: {uri}")

    @app.list_prompts()
    async def list_prompts() -> List[types.Prompt]:
        """List available prompts."""
        return [
            types.Prompt(
                name="fusion360_status",
                title="Check Fusion360 Status",
                description="Check the current connection status and setup of Fusion360MCP",
                arguments=[]
            ),
            types.Prompt(
                name="generate_part",
                title="Generate CAD Part",
                description="Generate a complete Fusion360 part from a natural language description",
                arguments=[
                    types.PromptArgument(
                        name="description",
                        description="Natural language description of the part to create",
                        required=True
                    ),
                    types.PromptArgument(
                        name="units",
                        description="Units to use (mm, inches, etc.)",
                        required=False
                    )
                ]
            ),
            types.Prompt(
                name="tutorial_workflow",
                title="Tutorial Workflow",
                description="Get a step-by-step tutorial for creating specific types of parts",
                arguments=[
                    types.PromptArgument(
                        name="part_type",
                        description="Type of part (bracket, enclosure, gear, etc.)",
                        required=True
                    )
                ]
            )
        ]

    @app.get_prompt()
    async def get_prompt(name: str, arguments: dict) -> types.GetPromptResult:
        """Handle prompt requests."""
        
        if name == "fusion360_status":
            # Check current status
            try:
                fusion360 = get_fusion360_connection()
                if fusion360:
                    scene_info = fusion360.send_command("get_scene_info")
                    status_text = f"""✅ **Fusion360MCP Status: Connected**

**Mode**: {mode}
**Design**: {scene_info.get('design_name', 'Unknown')}
**Bodies**: {scene_info.get('root_component', {}).get('bodies_count', 0)}
**Sketches**: {scene_info.get('root_component', {}).get('sketches_count', 0)}
**Features**: {scene_info.get('root_component', {}).get('features_count', 0)}

🎉 Ready for direct execution! You can now use Fusion360 tools directly."""
                else:
                    status_text = f"""❌ **Fusion360MCP Status: Disconnected**

**Mode**: {mode}

🔧 **To Connect:**
1. Make sure Fusion360 is running
2. Install the Fusion360MCP add-in
3. Click "Start MCP Server" in the Fusion360MCP panel
4. Try your command again"""
                    
            except Exception as e:
                status_text = f"""⚠️ **Fusion360MCP Status: Error**

**Mode**: {mode}
**Error**: {str(e)}

🔧 **Troubleshooting needed** - check the setup instructions."""
            
            return types.GetPromptResult(
                description="Fusion360MCP connection status",
                messages=[
                    types.PromptMessage(
                        role="assistant",
                        content=types.TextContent(type="text", text=status_text)
                    )
                ]
            )
        
        elif name == "generate_part":
            description = arguments.get("description", "")
            units = arguments.get("units", "mm")
            
            mode_note = "Commands will execute directly in Fusion360!" if mode == "socket" else "Commands will generate scripts for manual execution."
            
            return types.GetPromptResult(
                description=f"Generate Fusion360 part for: {description}",
                messages=[
                    types.PromptMessage(
                        role="user",
                        content=types.TextContent(
                            type="text",
                            text=f"""Please create a Fusion360 part with the following description: {description}

Use units: {units}

Break down the part creation into logical steps using the available Fusion360 tools:
- create_sketch: Start with sketches on appropriate planes
- draw_rectangle, draw_circle, draw_line: Create 2D geometry  
- extrude, revolve: Turn 2D sketches into 3D features
- fillet, chamfer: Add edge treatments
- shell, mirror: Add advanced features

Generate the appropriate tool calls in sequence to create this part. Each tool call should include all required parameters with realistic values.

**Mode**: {mode} - {mode_note}"""
                        )
                    )
                ]
            )
        
        elif name == "tutorial_workflow":
            part_type = arguments.get("part_type", "")
            
            tutorials = {
                "bracket": """L-Bracket Tutorial:
1. create_sketch(plane="xy") - Start with XY plane
2. draw_rectangle(width=40, height=30) - Main base
3. extrude(height=5) - Create base thickness
4. create_sketch(plane="yz") - Switch to YZ plane for vertical part
5. draw_rectangle(width=30, height=25, origin_z=5) - Vertical section
6. extrude(height=5, direction="positive") - Create vertical wall
7. fillet(radius=3, edge_selection="all") - Round all edges""",
                
                "enclosure": """Electronics Enclosure Tutorial:
1. create_sketch(plane="xy") - Base outline
2. draw_rectangle(width=80, height=60) - Outer dimensions
3. extrude(height=40) - Create solid block
4. shell(thickness=2, face_selection="top") - Hollow out with top open
5. create_sketch(plane="xy") - New sketch for mounting holes
6. draw_circle(radius=1.5, center_x=10, center_y=10) - Corner hole
7. draw_circle(radius=1.5, center_x=70, center_y=10) - Repeat for all corners
8. extrude(height=-2, operation="cut") - Cut mounting holes""",
                
                "gear": """Simple Gear Tutorial:
1. create_sketch(plane="xy") - Start with circular profile
2. draw_circle(radius=20) - Outer diameter
3. draw_circle(radius=5) - Center bore
4. extrude(height=8) - Create gear thickness
5. create_sketch(plane="xy") - Sketch for teeth (simplified)
6. draw_rectangle(width=2, height=8, origin_x=18) - Single tooth
7. revolve(angle=360, operation="cut") - Pattern around (simplified)
8. chamfer(distance=0.5, edge_selection="top") - Soften edges"""
            }
            
            tutorial_text = tutorials.get(part_type.lower(), f"No tutorial available for '{part_type}'. Available tutorials: {', '.join(tutorials.keys())}")
            
            mode_note = f"\n\n**Mode**: {mode} - {'Direct execution in Fusion360!' if mode == 'socket' else 'Copy scripts to Fusion360.'}"
            
            return types.GetPromptResult(
                description=f"Tutorial for creating a {part_type}",
                messages=[
                    types.PromptMessage(
                        role="assistant",
                        content=types.TextContent(
                            type="text",
                            text=tutorial_text + mode_note
                        )
                    )
                ]
            )
        
        else:
            raise ValueError(f"Unknown prompt: {name}")

    # Set up transport
    if transport == "sse":
        from mcp.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.responses import Response
        from starlette.routing import Mount, Route

        sse = SseServerTransport("/messages/")

        async def handle_sse(request):
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await app.run(
                    streams[0], streams[1], app.create_initialization_options()
                )
            return Response()

        starlette_app = Starlette(
            debug=True,
            routes=[
                Route("/sse", endpoint=handle_sse, methods=["GET"]),
                Mount("/messages/", app=sse.handle_post_message),
            ],
        )

        import uvicorn
        uvicorn.run(starlette_app, host="127.0.0.1", port=port)
    
    else:
        # stdio transport (default)
        from mcp.server.stdio import stdio_server

        async def arun():
            async with stdio_server() as streams:
                await app.run(
                    streams[0], streams[1], app.create_initialization_options()
                )

        anyio.run(arun)

    return 0 
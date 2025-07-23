# Fusion360 MCP Server

A modern Model Context Protocol (MCP) server for Autodesk Fusion 360, built from scratch using the latest MCP SDK. This server enables AI assistants to generate Fusion 360 Python scripts through natural language commands.

## 🚀 Features

- **Complete Tool Registry**: 13+ essential Fusion 360 tools including inspection, sketching, modeling, and finishing operations
- **Modern MCP Architecture**: Built with the latest MCP SDK patterns and best practices
- **Intelligent Script Generation**: Converts tool calls into production-ready Fusion 360 Python scripts
- **Resource System**: Access to tool documentation and examples
- **Prompt Templates**: Pre-built prompts for common CAD workflows
- **Multiple Transports**: Supports both stdio and SSE transport protocols

## 🛠️ Available Tools

### Inspection & Debugging Tools
- `get_scene_info` - Get detailed information about the current Fusion360 design
- `get_object_info` - Get detailed information about a specific object in the design
- `execute_code` - Execute arbitrary Python code in Fusion360 for debugging and advanced operations

### Sketching Tools
- `create_sketch` - Create sketches on XY, YZ, or XZ planes
- `draw_rectangle` - Draw rectangles with configurable dimensions
- `draw_circle` - Draw circles with specified radius and center
- `draw_line` - Draw lines between two points

### 3D Modeling Tools
- `extrude` - Extrude sketches into 3D geometry
- `revolve` - Revolve profiles around an axis
- `shell` - Create hollow shells from solid bodies
- `mirror` - Mirror features across construction planes

### Finishing Tools
- `fillet` - Add fillets to edges with smart edge selection
- `chamfer` - Add chamfers to edges

## 📋 Prerequisites

- Python 3.10 or higher
- Autodesk Fusion 360
- Access to the MCP SDK (included in this project)

## 🔧 Installation

1. **Clone or create the project directory:**
   ```bash
   mkdir fusion360-mcp
   cd fusion360-mcp
   ```

2. **Install dependencies using uv (recommended):**
   ```bash
   uv sync
   ```
   
   Or using pip:
   ```bash
   pip install -e .
   ```

3. **Verify installation:**
   ```bash
   fusion360-mcp --help
   ```

## 🔌 Fusion360 Add-in Installation (Optional)

For **direct execution** within Fusion360, install the included add-in:

1. **Copy the add-in folder:**
   - Navigate to your project's `fusion360_addon/` folder
   - Copy the entire `fusion360_addon/` folder

2. **Install in Fusion360:** (For Windows)
   - Paste it into: `C:\Users\[Your Username]\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\`
   - Rename the copied folder from `fusion360_addon` to `Fusion360MCP`

3. **Enable the add-in:**
   - Open Fusion360
   - Go to **Utilities** → **ADD-INS**
   - Find "Fusion360MCP" in the list and click **Run**
   - The add-in will create a "Fusion360MCP" panel in your toolbar

4. **Start the socket server:**
   - Click **"Start MCP Server"** in the Fusion360MCP panel
   - The add-in will start a socket server on `localhost:9876`

With the add-in installed, your MCP client can directly execute commands in Fusion360 without manual script copying!

## 🚀 Usage

### Running as MCP Server (Default)

For integration with Claude Desktop or other MCP clients:

```bash
fusion360-mcp
```

This starts the server in stdio mode, which is the standard for MCP client integration.

### Running as SSE Server

For web-based integration or testing:

```bash
fusion360-mcp --transport sse --port 8000
```

## 🔗 Claude Desktop Integration

Add this configuration to your Claude Desktop MCP settings:

```json
{
  "mcpServers": {
    "fusion360": {
      "command": "fusion360-mcp",
      "args": [],
      "env": {}
    }
  }
}
```

## 🎯 Example Workflows

### Creating a Simple Bracket
```
1. create_sketch(plane="xy")
2. draw_rectangle(width=40, height=30)
3. extrude(height=5)
4. create_sketch(plane="yz") 
5. draw_rectangle(width=30, height=25, origin_z=5)
6. extrude(height=5)
7. fillet(radius=3, edge_selection="all")
```

### Electronics Enclosure
```
1. create_sketch(plane="xy")
2. draw_rectangle(width=80, height=60)
3. extrude(height=40)
4. shell(thickness=2, face_selection="top")
5. create_sketch(plane="xy")
6. draw_circle(radius=1.5, center_x=10, center_y=10)
7. extrude(height=-2, operation="cut")
```

## 📚 Resources and Prompts

The server provides built-in resources and prompts:

### Resources
- `fusion360://tools` - Complete tool registry with schemas
- `fusion360://examples` - Example workflows and scripts

### Prompts
- `generate_part` - Generate parts from natural language descriptions
- `tutorial_workflow` - Get step-by-step tutorials for common parts

## 🔧 Script Output

All tool calls generate complete Fusion 360 Python scripts that can be:

1. **Copied and pasted** directly into Fusion 360's script editor
2. **Saved as .py files** and run as add-ins
3. **Integrated** into larger automation workflows

Example generated script:
```python
#Author-Fusion360 MCP Server
#Description-Auto-generated script from MCP tool calls

import adsk.core, adsk.fusion, adsk.cam, traceback

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        
        # Get the active design
        design = app.activeProduct
        component = design.rootComponent
        
        # Create a new sketch on the xy plane
        sketches = component.sketches
        xyPlane = component.xYConstructionPlane
        sketch = sketches.add(xyPlane)
        
        # Draw a rectangle
        rectangle = sketch.sketchCurves.sketchLines.addTwoPointRectangle(
            adsk.core.Point3D.create(0.0, 0.0, 0.0),
            adsk.core.Point3D.create(50, 30, 0.0)
        )
        
        # Extrude the profile
        prof = sketch.profiles.item(0)
        extrudes = component.features.extrudeFeatures
        extInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        distance = adsk.core.ValueInput.createByReal(10)
        extInput.setDistanceExtent(False, distance)
        extrude = extrudes.add(extInput)
        
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def stop(context):
    pass
```


### Adding New Tools

1. Add tool definition to `FUSION360_TOOLS` in `tools.py`
2. Add script template to `SCRIPT_TEMPLATES` in `script_generator.py`
3. Add any special handling logic in `generate_script()`

### Testing

Run the server locally:
```bash
python -m fusion360_mcp
```

Test with MCP client or SSE mode for web testing.

## 📄 License

MIT License - see the existing Fusion360 server implementation for reference.

## 🤝 Contributing

This server was built from scratch using the latest MCP SDK. Contributions are welcome for:

- Additional Fusion 360 tools
- Enhanced script generation
- Better error handling
- Documentation improvements

## 🔗 Related Projects

- [MCP Python SDK](../python-sdk/) - The official MCP SDK used by this server
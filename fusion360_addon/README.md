# Fusion360MCP Add-in

Socket server add-in for Fusion360 that enables direct execution of CAD commands from Claude AI via the Model Context Protocol (MCP).

## 🎯 What This Does

This add-in creates a **socket server inside Fusion360** that:
- ✅ Receives commands from the MCP server
- ✅ Executes Fusion360 API operations directly
- ✅ Returns real-time responses 
- ✅ No copy/paste scripts needed!

## 📥 Installation

### 1. Copy Add-in Files

Copy the entire `fusion360_addon` folder to your Fusion360 add-ins directory and rename it to `Fusion360MCP`:

```
C:\Users\Will\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\Fusion360MCP\
```

### 2. Enable Add-in in Fusion360

1. Open Fusion360
2. Go to **Utilities** → **ADD-INS** → **Scripts and Add-Ins**
3. Click **Add-Ins** tab
4. Find **"Fusion360MCP"** in the list
5. Check the box to enable it
6. Click **Run** to start the add-in

### 3. Verify Installation

You should see:
- ✅ A "Fusion360MCP" panel in the Fusion360 toolbar
- ✅ "Start MCP Server" and "Stop MCP Server" buttons
- ✅ Success message confirming add-in loaded

## 🚀 Usage

### Starting the Server

1. In Fusion360, find the **"Fusion360MCP"** toolbar panel
2. Click **"Start MCP Server"**
3. You'll see a confirmation: "✅ MCP Server started successfully!"
4. The server is now ready to receive commands from Claude/Cursor!

### Connecting from MCP Client

Once the server is running in Fusion360, your MCP client (Cursor) can connect and send commands like:

```python
# These commands now execute directly in Fusion360!
create_sketch(plane="xy")
draw_rectangle(width=50, height=30) 
extrude(height=15)
fillet(radius=5)
```

### Stopping the Server

Click **"Stop MCP Server"** when you're done to close the connection.

## 🔧 Available Commands

The add-in supports all the same commands as the MCP server:

### Design Information
- `get_scene_info` - Get current design info
- `get_object_info` - Get specific object details
- `execute_code` - Run arbitrary Fusion360 Python code

### Sketching
- `create_sketch` - Create new sketch
- `draw_rectangle` - Draw rectangles
- `draw_circle` - Draw circles  
- `draw_line` - Draw lines

### 3D Operations
- `extrude` - Extrude profiles
- `revolve` - Revolve around axis
- `fillet` - Round edges
- `chamfer` - Chamfer edges
- `shell` - Create hollow shells
- `mirror` - Mirror features

## 🔗 Integration with MCP Server

This add-in works with the updated MCP server that connects via socket instead of generating scripts. The workflow is:

```
Cursor/Claude → MCP Server → Socket Connection → Fusion360 Add-in → Direct Execution
```

## 🐛 Troubleshooting

### Add-in Won't Load
- Check that all files are in the correct directory
- Verify Fusion360 version compatibility (2603.0.86+)
- Look at the Fusion360 console for error messages

### Server Won't Start  
- Check if port 9876 is already in use
- Restart Fusion360 and try again
- Check Windows Firewall settings

### Commands Not Working
- Verify the MCP server is configured to connect to localhost:9876
- Check that Fusion360 has an active design document
- Look for error messages in the Fusion360 console

### Connection Issues
- Make sure only one MCP client is connected at a time
- Restart both the add-in and MCP server if connection is lost
- Check network/firewall settings if on a different machine

## 📁 File Structure

```
fusion360_addon/
├── Fusion360MCP.py          # Main add-in entry point
├── Fusion360MCP.manifest    # Add-in metadata
├── server/
│   ├── __init__.py          # Package init
│   ├── socket_server.py     # Socket server implementation
│   ├── command_handler.py   # Command execution logic
│   └── ui_panel.py         # UI controls
└── README.md               # This file
```

## 🔄 Installation Instructions for Users

After downloading this project from GitHub:

1. ✅ Navigate to the `fusion360_addon` folder
2. ✅ Copy the entire contents to your Fusion360 add-ins directory (rename the folder to `Fusion360MCP`)
3. ✅ Enable the add-in in Fusion360
4. ✅ Configure the MCP server to connect via socket (should be default)
5. 🎉 Enjoy direct Fusion360 control from AI!

## 📄 Version

- **Version**: 1.0.0
- **Fusion360**: 2603.0.86+
- **Protocol**: MCP Socket Connection
- **Port**: 9876 (default) 
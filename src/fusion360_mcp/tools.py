"""Fusion360 tool definitions and registry."""

import mcp.types as types
from typing import Dict, Any, List

# Tool registry defining all available Fusion360 tools
FUSION360_TOOLS = [
    {
        "name": "get_scene_info",
        "title": "Get Scene Info",
        "description": "Get detailed information about the current Fusion360 design",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_object_info", 
        "title": "Get Object Info",
        "description": "Get detailed information about a specific object in the design",
        "inputSchema": {
            "type": "object",
            "required": ["name"],
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name of the object to get information about"
                }
            }
        }
    },
    {
        "name": "execute_code",
        "title": "Execute Fusion360 Code",
        "description": "Execute arbitrary Python code in Fusion360 for debugging and advanced operations",
        "inputSchema": {
            "type": "object",
            "required": ["code"],
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python code to execute in Fusion360 context"
                }
            }
        }
    },
    {
        "name": "create_sketch",
        "title": "Create Sketch",
        "description": "Creates a new sketch on a specified plane in Fusion 360",
        "inputSchema": {
            "type": "object",
            "required": ["plane"],
            "properties": {
                "plane": {
                    "type": "string",
                    "enum": ["xy", "yz", "xz"],
                    "description": "The plane to create the sketch on"
                }
            }
        }
    },
    {
        "name": "draw_rectangle",
        "title": "Draw Rectangle",
        "description": "Draws a rectangle in the active sketch",
        "inputSchema": {
            "type": "object",
            "required": ["width", "height"],
            "properties": {
                "width": {
                    "type": "number",
                    "description": "Width of the rectangle in mm",
                    "minimum": 0.1
                },
                "height": {
                    "type": "number", 
                    "description": "Height of the rectangle in mm",
                    "minimum": 0.1
                },
                "origin_x": {
                    "type": "number",
                    "description": "X coordinate of the origin point",
                    "default": 0.0
                },
                "origin_y": {
                    "type": "number",
                    "description": "Y coordinate of the origin point", 
                    "default": 0.0
                },
                "origin_z": {
                    "type": "number",
                    "description": "Z coordinate of the origin point",
                    "default": 0.0
                }
            }
        }
    },
    {
        "name": "draw_circle",
        "title": "Draw Circle",
        "description": "Draws a circle in the active sketch",
        "inputSchema": {
            "type": "object",
            "required": ["radius"],
            "properties": {
                "radius": {
                    "type": "number",
                    "description": "Radius of the circle in mm",
                    "minimum": 0.1
                },
                "center_x": {
                    "type": "number",
                    "description": "X coordinate of the center point",
                    "default": 0.0
                },
                "center_y": {
                    "type": "number",
                    "description": "Y coordinate of the center point",
                    "default": 0.0
                },
                "center_z": {
                    "type": "number",
                    "description": "Z coordinate of the center point",
                    "default": 0.0
                }
            }
        }
    },
    {
        "name": "draw_line",
        "title": "Draw Line",
        "description": "Draws a line in the active sketch",
        "inputSchema": {
            "type": "object",
            "required": ["start_x", "start_y", "end_x", "end_y"],
            "properties": {
                "start_x": {
                    "type": "number",
                    "description": "X coordinate of the start point"
                },
                "start_y": {
                    "type": "number",
                    "description": "Y coordinate of the start point"
                },
                "start_z": {
                    "type": "number",
                    "description": "Z coordinate of the start point",
                    "default": 0.0
                },
                "end_x": {
                    "type": "number",
                    "description": "X coordinate of the end point"
                },
                "end_y": {
                    "type": "number",
                    "description": "Y coordinate of the end point"
                },
                "end_z": {
                    "type": "number",
                    "description": "Z coordinate of the end point",
                    "default": 0.0
                }
            }
        }
    },
    {
        "name": "extrude",
        "title": "Extrude",
        "description": "Extrudes a profile from a sketch",
        "inputSchema": {
            "type": "object",
            "required": ["height"],
            "properties": {
                "height": {
                    "type": "number",
                    "description": "Extrusion height in mm",
                    "minimum": 0.1
                },
                "profile_index": {
                    "type": "integer",
                    "description": "Index of the profile to extrude (0-based)",
                    "default": 0,
                    "minimum": 0
                },
                "operation": {
                    "type": "string",
                    "enum": ["new_body", "join", "cut", "intersect"],
                    "description": "Type of extrusion operation",
                    "default": "new_body"
                },
                "direction": {
                    "type": "string",
                    "enum": ["positive", "negative", "symmetric"],
                    "description": "Direction of extrusion",
                    "default": "positive"
                }
            }
        }
    },
    {
        "name": "revolve",
        "title": "Revolve",
        "description": "Revolves a profile around an axis",
        "inputSchema": {
            "type": "object",
            "required": ["angle"],
            "properties": {
                "angle": {
                    "type": "number",
                    "description": "Angle of revolution in degrees",
                    "minimum": 0.1,
                    "maximum": 360
                },
                "profile_index": {
                    "type": "integer",
                    "description": "Index of the profile to revolve (0-based)",
                    "default": 0,
                    "minimum": 0
                },
                "axis_origin_x": {
                    "type": "number",
                    "description": "X coordinate of the axis origin",
                    "default": 0.0
                },
                "axis_origin_y": {
                    "type": "number",
                    "description": "Y coordinate of the axis origin",
                    "default": 0.0
                },
                "axis_origin_z": {
                    "type": "number",
                    "description": "Z coordinate of the axis origin",
                    "default": 0.0
                },
                "axis_direction_x": {
                    "type": "number",
                    "description": "X component of the axis direction",
                    "default": 1.0
                },
                "axis_direction_y": {
                    "type": "number",
                    "description": "Y component of the axis direction",
                    "default": 0.0
                },
                "axis_direction_z": {
                    "type": "number",
                    "description": "Z component of the axis direction",
                    "default": 0.0
                },
                "operation": {
                    "type": "string",
                    "enum": ["new_body", "join", "cut", "intersect"],
                    "description": "Type of revolve operation",
                    "default": "new_body"
                }
            }
        }
    },
    {
        "name": "fillet",
        "title": "Fillet Edges",
        "description": "Creates a fillet on selected edges",
        "inputSchema": {
            "type": "object",
            "required": ["radius"],
            "properties": {
                "radius": {
                    "type": "number",
                    "description": "Fillet radius in mm",
                    "minimum": 0.1
                },
                "body_index": {
                    "type": "integer",
                    "description": "Index of the body to fillet (0-based)",
                    "default": 0,
                    "minimum": 0
                },
                "edge_selection": {
                    "type": "string",
                    "enum": ["all", "top", "bottom", "vertical"],
                    "description": "Which edges to fillet",
                    "default": "all"
                }
            }
        }
    },
    {
        "name": "chamfer",
        "title": "Chamfer Edges",
        "description": "Creates a chamfer on selected edges",
        "inputSchema": {
            "type": "object",
            "required": ["distance"],
            "properties": {
                "distance": {
                    "type": "number",
                    "description": "Chamfer distance in mm",
                    "minimum": 0.1
                },
                "body_index": {
                    "type": "integer",
                    "description": "Index of the body to chamfer (0-based)",
                    "default": 0,
                    "minimum": 0
                },
                "edge_selection": {
                    "type": "string",
                    "enum": ["all", "top", "bottom", "vertical"],
                    "description": "Which edges to chamfer",
                    "default": "all"
                }
            }
        }
    },
    {
        "name": "shell",
        "title": "Shell Body",
        "description": "Creates a hollow shell from a solid body",
        "inputSchema": {
            "type": "object",
            "required": ["thickness"],
            "properties": {
                "thickness": {
                    "type": "number",
                    "description": "Wall thickness in mm",
                    "minimum": 0.1
                },
                "body_index": {
                    "type": "integer",
                    "description": "Index of the body to shell (0-based)",
                    "default": 0,
                    "minimum": 0
                },
                "face_selection": {
                    "type": "string",
                    "enum": ["top", "bottom", "front", "back", "left", "right"],
                    "description": "Which face to remove for the shell",
                    "default": "top"
                }
            }
        }
    },
    {
        "name": "mirror",
        "title": "Mirror Feature",
        "description": "Creates a mirror of features across a plane",
        "inputSchema": {
            "type": "object",
            "required": ["mirror_plane"],
            "properties": {
                "mirror_plane": {
                    "type": "string",
                    "enum": ["xy", "yz", "xz"],
                    "description": "The plane to mirror across"
                },
                "body_index": {
                    "type": "integer",
                    "description": "Index of the body to mirror (0-based)",
                    "default": 0,
                    "minimum": 0
                }
            }
        }
    }
]


def get_tool_list() -> List[types.Tool]:
    """Convert tool registry to MCP Tool objects."""
    return [
        types.Tool(
            name=tool["name"],
            title=tool["title"], 
            description=tool["description"],
            inputSchema=tool["inputSchema"]
        )
        for tool in FUSION360_TOOLS
    ]


def get_tool_by_name(name: str) -> Dict[str, Any] | None:
    """Get tool definition by name."""
    for tool in FUSION360_TOOLS:
        if tool["name"] == name:
            return tool
    return None 
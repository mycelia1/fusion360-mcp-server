"""Script generator for Fusion360 MCP Server.

This module generates Fusion 360 Python scripts based on tool calls.
"""

from typing import Dict, Any, List
from .tools import get_tool_by_name


# Script templates for each tool
SCRIPT_TEMPLATES = {
    "create_sketch": """
# Create a new sketch on the {plane} plane
sketches = component.sketches
{plane_code}
sketch = sketches.add({plane_var})
""",

    "draw_rectangle": """
# Draw a rectangle
rectangle = sketch.sketchCurves.sketchLines.addTwoPointRectangle(
    adsk.core.Point3D.create({origin_x}, {origin_y}, {origin_z}),
    adsk.core.Point3D.create({origin_x} + {width}, {origin_y} + {height}, {origin_z})
)
""",

    "draw_circle": """
# Draw a circle
circle = sketch.sketchCurves.sketchCircles.addByCenterRadius(
    adsk.core.Point3D.create({center_x}, {center_y}, {center_z}),
    {radius}
)
""",

    "draw_line": """
# Draw a line
line = sketch.sketchCurves.sketchLines.addByTwoPoints(
    adsk.core.Point3D.create({start_x}, {start_y}, {start_z}),
    adsk.core.Point3D.create({end_x}, {end_y}, {end_z})
)
""",

    "extrude": """
# Extrude the profile
prof = sketch.profiles.item({profile_index})
extrudes = component.features.extrudeFeatures
extInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.{operation_code}FeatureOperation)
{direction_code}
extrude = extrudes.add(extInput)
""",

    "revolve": """
# Revolve the profile
prof = sketch.profiles.item({profile_index})
revolves = component.features.revolveFeatures
revInput = revolves.createInput(prof, adsk.fusion.FeatureOperations.{operation_code}FeatureOperation)
axis = adsk.core.Line3D.create(
    adsk.core.Point3D.create({axis_origin_x}, {axis_origin_y}, {axis_origin_z}),
    adsk.core.Vector3D.create({axis_direction_x}, {axis_direction_y}, {axis_direction_z})
)
revInput.setRevolutionExtent(False, adsk.core.ValueInput.createByString("{angle} deg"))
revInput.revolutionAxis = axis
revolve = revolves.add(revInput)
""",

    "fillet": """
# Fillet edges
fillets = component.features.filletFeatures
edgeCollection = adsk.core.ObjectCollection.create()
body = component.bRepBodies.item({body_index})
{edge_collection_code}
filletInput = fillets.createInput()
filletInput.addConstantRadiusEdgeSet(edgeCollection, adsk.core.ValueInput.createByReal({radius}), True)
fillet = fillets.add(filletInput)
""",

    "chamfer": """
# Chamfer edges
chamfers = component.features.chamferFeatures
edgeCollection = adsk.core.ObjectCollection.create()
body = component.bRepBodies.item({body_index})
{edge_collection_code}
chamferInput = chamfers.createInput(edgeCollection, True)
chamferInput.setToEqualDistance(adsk.core.ValueInput.createByReal({distance}))
chamfer = chamfers.add(chamferInput)
""",

    "shell": """
# Shell the body
shells = component.features.shellFeatures
body = component.bRepBodies.item({body_index})
faceCollection = adsk.core.ObjectCollection.create()
{face_collection_code}
# Create body collection (API expects ObjectCollection, not Python list)
bodyCollection = adsk.core.ObjectCollection.create()
bodyCollection.add(body)

# Create shell input with just the body collection, then set faces to remove as property
shellInput = shells.createInput(bodyCollection)
shellInput.facesToRemove = faceCollection
shellInput.insideThickness = adsk.core.ValueInput.createByReal({thickness})
shell = shells.add(shellInput)
""",

    "mirror": """
# Mirror feature
mirrors = component.features.mirrorFeatures
body = component.bRepBodies.item({body_index})
inputEntities = adsk.core.ObjectCollection.create()
inputEntities.add(body)
{mirror_plane_code}
mirrorInput = mirrors.createInput(inputEntities, {mirror_plane_var})
mirror = mirrors.add(mirrorInput)
"""
}


def _get_plane_code(plane: str) -> tuple[str, str]:
    """Get the plane code and variable for sketch creation."""
    plane_map = {
        "xy": ("xyPlane = component.xYConstructionPlane", "xyPlane"),
        "yz": ("yzPlane = component.yZConstructionPlane", "yzPlane"), 
        "xz": ("xzPlane = component.xZConstructionPlane", "xzPlane")
    }
    return plane_map.get(plane, plane_map["xy"])


def _get_operation_code(operation: str) -> str:
    """Get the operation code for features."""
    operation_map = {
        "new_body": "NewBody",
        "join": "Join",
        "cut": "Cut", 
        "intersect": "Intersect"
    }
    return operation_map.get(operation, "NewBody")


def _get_direction_code(direction: str, height: float) -> str:
    """Get the direction code for extrude operations."""
    if direction == "positive":
        return f"distance = adsk.core.ValueInput.createByReal({height})\nextInput.setDistanceExtent(False, distance)"
    elif direction == "negative":
        return f"distance = adsk.core.ValueInput.createByReal(-{height})\nextInput.setDistanceExtent(False, distance)"
    elif direction == "symmetric":
        return f"distance = adsk.core.ValueInput.createByReal({height/2})\nextInput.setSymmetricExtent(distance, True)"
    else:
        return f"distance = adsk.core.ValueInput.createByReal({height})\nextInput.setDistanceExtent(False, distance)"


def _get_edge_collection_code(edge_selection: str) -> str:
    """Get edge collection code for fillet/chamfer operations."""
    if edge_selection == "all":
        return """for edge in body.edges:
    edgeCollection.add(edge)"""
    elif edge_selection == "top":
        return """for edge in body.edges:
    if edge.boundingBox.maxPoint.z > (body.boundingBox.maxPoint.z - 0.001):
        edgeCollection.add(edge)"""
    elif edge_selection == "bottom":
        return """for edge in body.edges:
    if edge.boundingBox.minPoint.z < (body.boundingBox.minPoint.z + 0.001):
        edgeCollection.add(edge)"""
    elif edge_selection == "vertical":
        return """for edge in body.edges:
    # Select edges that are approximately vertical
    direction = edge.geometry.direction
    if abs(direction.z) < 0.1:  # Nearly horizontal
        edgeCollection.add(edge)"""
    else:
        return """for edge in body.edges:
    edgeCollection.add(edge)"""


def _get_face_collection_code(face_selection: str) -> str:
    """Get face collection code for shell operations."""
    face_map = {
        "top": """for face in body.faces:
    if face.boundingBox.maxPoint.z > (body.boundingBox.maxPoint.z - 0.001):
        faceCollection.add(face)""",
        "bottom": """for face in body.faces:
    if face.boundingBox.minPoint.z < (body.boundingBox.minPoint.z + 0.001):
        faceCollection.add(face)""",
        "front": """for face in body.faces:
    if face.boundingBox.maxPoint.y > (body.boundingBox.maxPoint.y - 0.001):
        faceCollection.add(face)""",
        "back": """for face in body.faces:
    if face.boundingBox.minPoint.y < (body.boundingBox.minPoint.y + 0.001):
        faceCollection.add(face)""",
        "left": """for face in body.faces:
    if face.boundingBox.minPoint.x < (body.boundingBox.minPoint.x + 0.001):
        faceCollection.add(face)""",
        "right": """for face in body.faces:
    if face.boundingBox.maxPoint.x > (body.boundingBox.maxPoint.x - 0.001):
        faceCollection.add(face)"""
    }
    return face_map.get(face_selection, face_map["top"])


def _get_mirror_plane_code(mirror_plane: str) -> tuple[str, str]:
    """Get mirror plane code and variable."""
    plane_map = {
        "xy": ("xyPlane = component.xYConstructionPlane", "xyPlane"),
        "yz": ("yzPlane = component.yZConstructionPlane", "yzPlane"),
        "xz": ("xzPlane = component.xZConstructionPlane", "xzPlane")
    }
    return plane_map.get(mirror_plane, plane_map["xy"])


def generate_script(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Generate a Fusion 360 script for a single tool call."""
    tool_def = get_tool_by_name(tool_name)
    if not tool_def:
        raise ValueError(f"Unknown tool: {tool_name}")
    
    template = SCRIPT_TEMPLATES.get(tool_name)
    if not template:
        raise ValueError(f"No script template for tool: {tool_name}")
    
    # Process arguments with defaults and special handling
    processed_args = {}
    
    # Copy all arguments
    for key, value in arguments.items():
        processed_args[key] = value
    
    # Apply defaults from tool schema
    tool_props = tool_def["inputSchema"]["properties"]
    for prop_name, prop_def in tool_props.items():
        if prop_name not in processed_args and "default" in prop_def:
            processed_args[prop_name] = prop_def["default"]
    
    # Special handling for specific tools
    if tool_name == "create_sketch":
        plane_code, plane_var = _get_plane_code(processed_args.get("plane", "xy"))
        processed_args["plane_code"] = plane_code
        processed_args["plane_var"] = plane_var
    
    elif tool_name == "extrude":
        operation_code = _get_operation_code(processed_args.get("operation", "new_body"))
        processed_args["operation_code"] = operation_code
        direction_code = _get_direction_code(
            processed_args.get("direction", "positive"),
            processed_args.get("height", 10.0)
        )
        processed_args["direction_code"] = direction_code
    
    elif tool_name == "revolve":
        operation_code = _get_operation_code(processed_args.get("operation", "new_body"))
        processed_args["operation_code"] = operation_code
    
    elif tool_name in ["fillet", "chamfer"]:
        edge_collection_code = _get_edge_collection_code(
            processed_args.get("edge_selection", "all")
        )
        processed_args["edge_collection_code"] = edge_collection_code
    
    elif tool_name == "shell":
        face_collection_code = _get_face_collection_code(
            processed_args.get("face_selection", "top")
        )
        processed_args["face_collection_code"] = face_collection_code
    
    elif tool_name == "mirror":
        mirror_plane_code, mirror_plane_var = _get_mirror_plane_code(
            processed_args.get("mirror_plane", "xy")
        )
        processed_args["mirror_plane_code"] = mirror_plane_code
        processed_args["mirror_plane_var"] = mirror_plane_var
    
    # Format the template
    try:
        return template.format(**processed_args)
    except KeyError as e:
        raise ValueError(f"Missing required parameter for {tool_name}: {e}")


def generate_multi_tool_script(tool_calls: List[Dict[str, Any]]) -> str:
    """Generate a complete Fusion 360 script for multiple tool calls."""
    script_parts = []
    
    # Add script header
    script_parts.append("""#Author-Fusion360 MCP Server
#Description-Auto-generated script from MCP tool calls

import adsk.core, adsk.fusion, adsk.cam, traceback

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        
        # Get the active design
        design = app.activeProduct
        if not design:
            ui.messageBox('No active Fusion design', 'No Design')
            return
            
        # Get the root component
        component = design.rootComponent
        
        # Variables for sketch and features
        sketch = None
""")
    
    # Add each tool call
    for i, tool_call in enumerate(tool_calls):
        tool_name = tool_call.get("tool_name") or tool_call.get("name")
        arguments = tool_call.get("arguments") or tool_call.get("parameters", {})
        
        try:
            tool_script = generate_script(tool_name, arguments)
            script_parts.append(f"        # Tool call {i+1}: {tool_name}")
            script_parts.append(tool_script)
        except Exception as e:
            script_parts.append(f"        # Error in tool call {i+1} ({tool_name}): {str(e)}")
    
    # Add script footer
    script_parts.append("""
        # Finish sketch if one is active
        if sketch and sketch.isValid:
            sketch.exitEdit()
            
    except:
        if ui:
            ui.messageBox('Failed:\\n{}'.format(traceback.format_exc()))

def stop(context):
    pass
""")
    
    return "\n".join(script_parts)


def generate_single_tool_script(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Generate a complete Fusion 360 script for a single tool call."""
    return generate_multi_tool_script([{"tool_name": tool_name, "arguments": arguments}]) 
"""
Fusion360 Command Handler

Handles execution of commands received from the MCP server.
Similar to the Blender addon's command execution but using Fusion360 API.
"""

import adsk.core
import adsk.fusion
import adsk.cam
import json
import traceback
import io
from contextlib import redirect_stdout

class CommandHandler:
    """Handles execution of commands in Fusion360"""
    
    def __init__(self):
        self.app = adsk.core.Application.get()
        self.ui = self.app.userInterface
        
    def execute_command(self, command):
        """Execute a command and return response"""
        try:
            return self._execute_command_internal(command)
        except Exception as e:
            print(f"Error executing command: {str(e)}")
            traceback.print_exc()
            return {"status": "error", "message": str(e)}
    
    def _execute_command_internal(self, command):
        """Internal command execution"""
        cmd_type = command.get("type")
        params = command.get("params", {})
        
        # Command handlers
        handlers = {
            "get_scene_info": self.get_scene_info,
            "get_object_info": self.get_object_info,
            "execute_code": self.execute_code,
            "create_sketch": self.create_sketch,
            "draw_rectangle": self.draw_rectangle,
            "draw_circle": self.draw_circle,
            "draw_line": self.draw_line,
            "extrude": self.extrude,
            "revolve": self.revolve,
            "fillet": self.fillet,
            "chamfer": self.chamfer,
            "shell": self.shell,
            "mirror": self.mirror,
        }
        
        handler = handlers.get(cmd_type)
        if handler:
            try:
                print(f"Executing handler for {cmd_type}")
                result = handler(**params)
                print(f"Handler execution complete")
                return {"status": "success", "result": result}
            except Exception as e:
                print(f"Error in handler: {str(e)}")
                traceback.print_exc()
                return {"status": "error", "message": str(e)}
        else:
            return {"status": "error", "message": f"Unknown command type: {cmd_type}"}
    
    def get_scene_info(self):
        """Get information about the current Fusion360 design"""
        try:
            design = self.app.activeProduct
            if not design:
                return {"error": "No active design"}
            
            # Get root component
            root_component = design.rootComponent
            
            info = {
                "design_name": design.parentDocument.name,
                "design_type": design.productType,
                "root_component": {
                    "name": root_component.name,
                    "bodies_count": root_component.bRepBodies.count,
                    "sketches_count": root_component.sketches.count,
                    "features_count": root_component.features.count,
                    "occurrences_count": root_component.occurrences.count
                },
                "timeline_count": design.timeline.count if hasattr(design, 'timeline') else 0,
                "camera": self._get_camera_info()
            }
            
            # Get bodies info
            bodies = []
            for i in range(root_component.bRepBodies.count):
                body = root_component.bRepBodies.item(i)
                bodies.append({
                    "name": body.name,
                    "volume": body.volume,
                    "area": body.area,
                    "material": body.material.name if body.material else "None",
                    "is_visible": body.isVisible
                })
            info["bodies"] = bodies
            
            return info
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_object_info(self, name):
        """Get detailed information about a specific object"""
        try:
            design = self.app.activeProduct
            if not design:
                return {"error": "No active design"}
            
            root_component = design.rootComponent
            
            # Try to find the object by name
            obj_info = {"name": name, "found": False}
            
            # Check bodies
            for i in range(root_component.bRepBodies.count):
                body = root_component.bRepBodies.item(i)
                if body.name == name:
                    obj_info.update({
                        "found": True,
                        "type": "body",
                        "volume": body.volume,
                        "area": body.area,
                        "material": body.material.name if body.material else "None",
                        "is_visible": body.isVisible,
                        "faces_count": body.faces.count,
                        "edges_count": body.edges.count,
                        "vertices_count": body.vertices.count
                    })
                    break
            
            # Check sketches if not found
            if not obj_info["found"]:
                for i in range(root_component.sketches.count):
                    sketch = root_component.sketches.item(i)
                    if sketch.name == name:
                        obj_info.update({
                            "found": True,
                            "type": "sketch",
                            "is_visible": sketch.isVisible,
                            "profile_count": sketch.profiles.count,
                            "curve_count": sketch.sketchCurves.count,
                            "plane": sketch.referencePlane.name if sketch.referencePlane else "Unknown"
                        })
                        break
            
            return obj_info
            
        except Exception as e:
            return {"error": str(e)}
    
    def execute_code(self, code):
        """Execute arbitrary Fusion360 Python code"""
        try:
            # Create namespace with Fusion360 modules
            namespace = {
                "adsk": adsk,
                "app": self.app,
                "ui": self.ui,
                "design": self.app.activeProduct
            }
            
            # Add root component if available
            if self.app.activeProduct:
                namespace["component"] = self.app.activeProduct.rootComponent
            
            # Capture output
            capture_buffer = io.StringIO()
            with redirect_stdout(capture_buffer):
                exec(code, namespace)
            
            captured_output = capture_buffer.getvalue()
            return {"executed": True, "result": captured_output}
            
        except Exception as e:
            raise Exception(f"Code execution error: {str(e)}")
    
    def create_sketch(self, plane="xy"):
        """Create a new sketch"""
        try:
            design = self.app.activeProduct
            root_component = design.rootComponent
            
            # Get the construction plane
            plane_map = {
                "xy": root_component.xYConstructionPlane,
                "yz": root_component.yZConstructionPlane,
                "xz": root_component.xZConstructionPlane
            }
            
            construction_plane = plane_map.get(plane, root_component.xYConstructionPlane)
            
            # Create the sketch
            sketch = root_component.sketches.add(construction_plane)
            
            return {
                "sketch_name": sketch.name,
                "plane": plane,
                "success": True
            }
            
        except Exception as e:
            raise Exception(f"Failed to create sketch: {str(e)}")
    
    def draw_rectangle(self, width, height, origin_x=0, origin_y=0, origin_z=0):
        """Draw a rectangle in the active sketch"""
        try:
            design = self.app.activeProduct
            root_component = design.rootComponent
            
            # Get the last sketch (most recently created)
            if root_component.sketches.count == 0:
                raise Exception("No sketch available. Create a sketch first.")
            
            sketch = root_component.sketches.item(root_component.sketches.count - 1)
            
            # Create rectangle points
            point1 = adsk.core.Point3D.create(origin_x, origin_y, origin_z)
            point2 = adsk.core.Point3D.create(origin_x + width, origin_y + height, origin_z)
            
            # Draw rectangle
            rectangle = sketch.sketchCurves.sketchLines.addTwoPointRectangle(point1, point2)
            
            return {
                "rectangle_created": True,
                "width": width,
                "height": height,
                "sketch": sketch.name
            }
            
        except Exception as e:
            raise Exception(f"Failed to draw rectangle: {str(e)}")
    
    def draw_circle(self, radius, center_x=0, center_y=0, center_z=0):
        """Draw a circle in the active sketch"""
        try:
            design = self.app.activeProduct
            root_component = design.rootComponent
            
            # Get the last sketch
            if root_component.sketches.count == 0:
                raise Exception("No sketch available. Create a sketch first.")
            
            sketch = root_component.sketches.item(root_component.sketches.count - 1)
            
            # Create center point
            center_point = adsk.core.Point3D.create(center_x, center_y, center_z)
            
            # Draw circle
            circle = sketch.sketchCurves.sketchCircles.addByCenterRadius(center_point, radius)
            
            return {
                "circle_created": True,
                "radius": radius,
                "center": [center_x, center_y, center_z],
                "sketch": sketch.name
            }
            
        except Exception as e:
            raise Exception(f"Failed to draw circle: {str(e)}")
    
    def draw_line(self, start_x, start_y, end_x, end_y, start_z=0, end_z=0):
        """Draw a line in the active sketch"""
        try:
            design = self.app.activeProduct
            root_component = design.rootComponent
            
            # Get the last sketch
            if root_component.sketches.count == 0:
                raise Exception("No sketch available. Create a sketch first.")
            
            sketch = root_component.sketches.item(root_component.sketches.count - 1)
            
            # Create points
            start_point = adsk.core.Point3D.create(start_x, start_y, start_z)
            end_point = adsk.core.Point3D.create(end_x, end_y, end_z)
            
            # Draw line
            line = sketch.sketchCurves.sketchLines.addByTwoPoints(start_point, end_point)
            
            return {
                "line_created": True,
                "start": [start_x, start_y, start_z],
                "end": [end_x, end_y, end_z],
                "sketch": sketch.name
            }
            
        except Exception as e:
            raise Exception(f"Failed to draw line: {str(e)}")
    
    def extrude(self, height, profile_index=0, operation="new_body", direction="positive"):
        """Extrude a profile"""
        try:
            design = self.app.activeProduct
            root_component = design.rootComponent
            
            # Get the last sketch
            if root_component.sketches.count == 0:
                raise Exception("No sketch available.")
            
            sketch = root_component.sketches.item(root_component.sketches.count - 1)
            
            # Get profile
            if sketch.profiles.count == 0:
                raise Exception("No profiles found in sketch.")
            
            profile = sketch.profiles.item(profile_index)
            
            # Create extrude input
            extrudes = root_component.features.extrudeFeatures
            
            # Set operation type
            operation_map = {
                "new_body": adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
                "join": adsk.fusion.FeatureOperations.JoinFeatureOperation,
                "cut": adsk.fusion.FeatureOperations.CutFeatureOperation,
                "intersect": adsk.fusion.FeatureOperations.IntersectFeatureOperation
            }
            
            operation_type = operation_map.get(operation, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            
            extrude_input = extrudes.createInput(profile, operation_type)
            
            # Set distance
            distance_value = adsk.core.ValueInput.createByReal(height)
            
            if direction == "symmetric":
                extrude_input.setSymmetricExtent(distance_value, True)
            else:
                is_negative = direction == "negative"
                extrude_input.setDistanceExtent(is_negative, distance_value)
            
            # Create the extrude
            extrude = extrudes.add(extrude_input)
            
            return {
                "extrude_created": True,
                "height": height,
                "operation": operation,
                "direction": direction,
                "feature_name": extrude.name
            }
            
        except Exception as e:
            raise Exception(f"Failed to extrude: {str(e)}")
    
    def revolve(self, angle, profile_index=0, axis_origin_x=0, axis_origin_y=0, axis_origin_z=0, 
                axis_direction_x=1, axis_direction_y=0, axis_direction_z=0, operation="new_body"):
        """Revolve a profile around an axis"""
        try:
            design = self.app.activeProduct
            root_component = design.rootComponent
            
            # Get the last sketch
            if root_component.sketches.count == 0:
                raise Exception("No sketch available.")
            
            sketch = root_component.sketches.item(root_component.sketches.count - 1)
            
            # Get profile
            if sketch.profiles.count == 0:
                raise Exception("No profiles found in sketch.")
            
            profile = sketch.profiles.item(profile_index)
            
            # Create revolve input
            revolves = root_component.features.revolveFeatures
            
            # Set operation type
            operation_map = {
                "new_body": adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
                "join": adsk.fusion.FeatureOperations.JoinFeatureOperation,
                "cut": adsk.fusion.FeatureOperations.CutFeatureOperation,
                "intersect": adsk.fusion.FeatureOperations.IntersectFeatureOperation
            }
            
            operation_type = operation_map.get(operation, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            
            revolve_input = revolves.createInput(profile, operation_type)
            
            # Create axis
            axis_point = adsk.core.Point3D.create(axis_origin_x, axis_origin_y, axis_origin_z)
            axis_direction = adsk.core.Vector3D.create(axis_direction_x, axis_direction_y, axis_direction_z)
            axis = adsk.core.Line3D.create(axis_point, axis_direction)
            
            # Set revolve extent
            angle_value = adsk.core.ValueInput.createByString(f"{angle} deg")
            revolve_input.setRevolutionExtent(False, angle_value)
            revolve_input.revolutionAxis = axis
            
            # Create the revolve
            revolve = revolves.add(revolve_input)
            
            return {
                "revolve_created": True,
                "angle": angle,
                "operation": operation,
                "feature_name": revolve.name
            }
            
        except Exception as e:
            raise Exception(f"Failed to revolve: {str(e)}")
    
    def fillet(self, radius, body_index=0, edge_selection="all"):
        """Create fillet on edges"""
        try:
            design = self.app.activeProduct
            root_component = design.rootComponent
            
            # Get body
            if root_component.bRepBodies.count == 0:
                raise Exception("No bodies available for filleting.")
            
            body = root_component.bRepBodies.item(body_index)
            
            # Create edge collection
            edge_collection = adsk.core.ObjectCollection.create()
            
            # Add edges based on selection
            if edge_selection == "all":
                for edge in body.edges:
                    edge_collection.add(edge)
            elif edge_selection == "top":
                bbox = body.boundingBox
                for edge in body.edges:
                    if edge.boundingBox.maxPoint.z > (bbox.maxPoint.z - 0.001):
                        edge_collection.add(edge)
            # Add more edge selection logic as needed
            
            # Create fillet
            fillets = root_component.features.filletFeatures
            fillet_input = fillets.createInput()
            fillet_input.addConstantRadiusEdgeSet(edge_collection, adsk.core.ValueInput.createByReal(radius), True)
            fillet = fillets.add(fillet_input)
            
            return {
                "fillet_created": True,
                "radius": radius,
                "edges_count": edge_collection.count,
                "feature_name": fillet.name
            }
            
        except Exception as e:
            raise Exception(f"Failed to create fillet: {str(e)}")
    
    def chamfer(self, distance, body_index=0, edge_selection="all"):
        """Create chamfer on edges"""
        try:
            design = self.app.activeProduct
            root_component = design.rootComponent
            
            # Get body
            if root_component.bRepBodies.count == 0:
                raise Exception("No bodies available for chamfering.")
            
            body = root_component.bRepBodies.item(body_index)
            
            # Create edge collection
            edge_collection = adsk.core.ObjectCollection.create()
            
            # Add edges based on selection
            if edge_selection == "all":
                for edge in body.edges:
                    edge_collection.add(edge)
            # Add more edge selection logic as needed
            
            # Create chamfer
            chamfers = root_component.features.chamferFeatures
            chamfer_input = chamfers.createInput(edge_collection, True)
            chamfer_input.setToEqualDistance(adsk.core.ValueInput.createByReal(distance))
            chamfer = chamfers.add(chamfer_input)
            
            return {
                "chamfer_created": True,
                "distance": distance,
                "edges_count": edge_collection.count,
                "feature_name": chamfer.name
            }
            
        except Exception as e:
            raise Exception(f"Failed to create chamfer: {str(e)}")
    
    def shell(self, thickness, body_index=0, face_selection="top"):
        """Create shell from body"""
        try:
            design = self.app.activeProduct
            root_component = design.rootComponent
            
            # Get body
            if root_component.bRepBodies.count == 0:
                raise Exception("No bodies available for shelling.")
            
            body = root_component.bRepBodies.item(body_index)
            
            # Create face collection for removal
            face_collection = adsk.core.ObjectCollection.create()
            
            # Add faces based on selection
            if face_selection == "top":
                bbox = body.boundingBox
                for face in body.faces:
                    if face.boundingBox.maxPoint.z > (bbox.maxPoint.z - 0.001):
                        face_collection.add(face)
            # Add more face selection logic as needed
            
            # Create shell
            shells = root_component.features.shellFeatures
            
            # Create body collection (API expects ObjectCollection, not Python list)
            body_collection = adsk.core.ObjectCollection.create()
            body_collection.add(body)
            
            # Create shell input with just the body collection
            shell_input = shells.createInput(body_collection)
            
            # Set the faces to remove as a property on the input
            shell_input.facesToRemove = face_collection
            
            # Set the thickness
            shell_input.insideThickness = adsk.core.ValueInput.createByReal(thickness)
            
            shell = shells.add(shell_input)
            
            return {
                "shell_created": True,
                "thickness": thickness,
                "faces_removed": face_collection.count,
                "feature_name": shell.name
            }
            
        except Exception as e:
            raise Exception(f"Failed to create shell: {str(e)}")
    
    def mirror(self, mirror_plane, body_index=0):
        """Mirror features across a plane"""
        try:
            design = self.app.activeProduct
            root_component = design.rootComponent
            
            # Get body
            if root_component.bRepBodies.count == 0:
                raise Exception("No bodies available for mirroring.")
            
            body = root_component.bRepBodies.item(body_index)
            
            # Get mirror plane
            plane_map = {
                "xy": root_component.xYConstructionPlane,
                "yz": root_component.yZConstructionPlane,
                "xz": root_component.xZConstructionPlane
            }
            
            construction_plane = plane_map.get(mirror_plane, root_component.xYConstructionPlane)
            
            # Create entity collection
            input_entities = adsk.core.ObjectCollection.create()
            input_entities.add(body)
            
            # Create mirror
            mirrors = root_component.features.mirrorFeatures
            mirror_input = mirrors.createInput(input_entities, construction_plane)
            mirror = mirrors.add(mirror_input)
            
            return {
                "mirror_created": True,
                "mirror_plane": mirror_plane,
                "feature_name": mirror.name
            }
            
        except Exception as e:
            raise Exception(f"Failed to create mirror: {str(e)}")
    
    def _get_camera_info(self):
        """Get camera information"""
        try:
            viewport = self.app.activeViewport
            camera = viewport.camera
            
            return {
                "eye": [camera.eye.x, camera.eye.y, camera.eye.z],
                "target": [camera.target.x, camera.target.y, camera.target.z],
                "up_vector": [camera.upVector.x, camera.upVector.y, camera.upVector.z],
                "camera_type": camera.cameraType,
                "is_smooth_transition": camera.isSmoothTransition
            }
        except:
            return {"error": "Could not get camera info"} 
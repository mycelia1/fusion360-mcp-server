#!/usr/bin/env python3
"""
Simple example demonstrating the Fusion360 MCP Server.

This script shows how to interact with the server programmatically
to generate Fusion360 scripts for a simple box with rounded edges.
"""

import asyncio
import json
from typing import List, Dict, Any

from fusion360_mcp.server import main
from fusion360_mcp.tools import get_tool_list
from fusion360_mcp.script_generator import generate_multi_tool_script


async def example_simple_box():
    """Example: Create a simple box with filleted edges."""
    
    print("🚀 Fusion360 MCP Server Example")
    print("=" * 50)
    
    # Show available tools
    tools = get_tool_list()
    print(f"Available tools: {len(tools)}")
    for tool in tools[:5]:  # Show first 5 tools
        print(f"  - {tool.name}: {tool.description}")
    print("  ...")
    print()
    
    # Define the tool calls for a simple box
    tool_calls = [
        {
            "tool_name": "create_sketch",
            "arguments": {"plane": "xy"}
        },
        {
            "tool_name": "draw_rectangle", 
            "arguments": {
                "width": 50,
                "height": 30,
                "origin_x": 0,
                "origin_y": 0
            }
        },
        {
            "tool_name": "extrude",
            "arguments": {
                "height": 20,
                "operation": "new_body"
            }
        },
        {
            "tool_name": "fillet",
            "arguments": {
                "radius": 3,
                "edge_selection": "top"
            }
        }
    ]
    
    print("📋 Workflow: Simple Box with Filleted Edges")
    print("-" * 40)
    for i, call in enumerate(tool_calls, 1):
        tool_name = call["tool_name"]
        args = call["arguments"]
        print(f"{i}. {tool_name}({', '.join(f'{k}={v}' for k, v in args.items())})")
    print()
    
    # Generate the script
    print("🔧 Generating Fusion360 script...")
    script = generate_multi_tool_script(tool_calls)
    
    print("✅ Generated script:")
    print("=" * 60)
    print(script)
    print("=" * 60)
    
    # Save the script to a file
    output_file = "simple_box_example.py"
    with open(output_file, 'w') as f:
        f.write(script)
    
    print(f"💾 Script saved to: {output_file}")
    print("🎯 Copy this script to Fusion360's script editor and run!")


async def example_complex_part():
    """Example: Create a more complex part with multiple operations."""
    
    print("\n" + "=" * 60)
    print("🏗️  Complex Part Example: Electronics Enclosure")
    print("=" * 60)
    
    tool_calls = [
        # Create base
        {"tool_name": "create_sketch", "arguments": {"plane": "xy"}},
        {"tool_name": "draw_rectangle", "arguments": {"width": 80, "height": 60}},
        {"tool_name": "extrude", "arguments": {"height": 40}},
        
        # Shell the enclosure
        {"tool_name": "shell", "arguments": {"thickness": 2, "face_selection": "top"}},
        
        # Add mounting holes
        {"tool_name": "create_sketch", "arguments": {"plane": "xy"}},
        {"tool_name": "draw_circle", "arguments": {"radius": 1.5, "center_x": 10, "center_y": 10}},
        {"tool_name": "draw_circle", "arguments": {"radius": 1.5, "center_x": 70, "center_y": 10}},
        {"tool_name": "draw_circle", "arguments": {"radius": 1.5, "center_x": 10, "center_y": 50}},
        {"tool_name": "draw_circle", "arguments": {"radius": 1.5, "center_x": 70, "center_y": 50}},
        {"tool_name": "extrude", "arguments": {"height": -5, "operation": "cut"}},
        
        # Add chamfers
        {"tool_name": "chamfer", "arguments": {"distance": 1, "edge_selection": "top"}}
    ]
    
    print("📋 Workflow Steps:")
    for i, call in enumerate(tool_calls, 1):
        tool_name = call["tool_name"]
        args = call["arguments"]
        args_str = ", ".join(f"{k}={v}" for k, v in args.items())
        print(f"{i:2d}. {tool_name}({args_str})")
    
    # Generate script
    script = generate_multi_tool_script(tool_calls)
    
    # Save to file
    output_file = "electronics_enclosure_example.py"
    with open(output_file, 'w') as f:
        f.write(script)
    
    print(f"\n💾 Complex script saved to: {output_file}")


def show_tool_details():
    """Show detailed information about all available tools."""
    
    print("\n" + "=" * 60)
    print("🔧 Detailed Tool Information")
    print("=" * 60)
    
    tools = get_tool_list()
    
    for tool in tools:
        print(f"\n📦 {tool.name} ({tool.title})")
        print(f"   {tool.description}")
        
        # Show required parameters
        schema = tool.inputSchema
        if "required" in schema:
            required = ", ".join(schema["required"])
            print(f"   Required: {required}")
        
        # Show optional parameters with defaults
        props = schema.get("properties", {})
        optional = []
        for prop_name, prop_def in props.items():
            if prop_name not in schema.get("required", []):
                default = prop_def.get("default", "no default")
                optional.append(f"{prop_name}({default})")
        
        if optional:
            print(f"   Optional: {', '.join(optional)}")


async def main_example():
    """Run all examples."""
    
    # Simple box example
    await example_simple_box()
    
    # Complex part example  
    await example_complex_part()
    
    # Tool details
    show_tool_details()
    
    print("\n" + "=" * 60)
    print("🎉 Examples completed!")
    print("📝 Check the generated .py files and copy them to Fusion360")
    print("🔗 Or integrate this server with Claude Desktop for AI-powered CAD!")


if __name__ == "__main__":
    asyncio.run(main_example()) 
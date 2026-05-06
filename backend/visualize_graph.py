"""
Visualize the knowledge graph from knowledge_map.json
Creates an interactive, beautiful HTML visualization with tree layout.
Handles multiple disconnected graphs by stacking them vertically.
Groups web sources under a proxy node to reduce clutter.

Usage:
    python visualize_graph.py [optional_json_file]
"""

import json
import os
import sys
import glob
import shutil
from typing import List, Dict, Set


def load_graph(filepath: str) -> dict:
    """Load the knowledge graph JSON."""
    with open(filepath, 'r') as f:
        return json.load(f)


def get_connected_subgraphs(graph_data: dict) -> List[dict]:
    """Split the graph into connected components (subgraphs)."""
    nodes_map = {n['id']: n for n in graph_data['nodes']}
    # Build undirected adjacency for connectivity check
    adjacency: Dict[str, Set[str]] = {n_id: set() for n_id in nodes_map}

    for edge in graph_data['edges']:
        src, tgt = edge['source'], edge['target']
        if src in nodes_map and tgt in nodes_map:
            adjacency[src].add(tgt)
            adjacency[tgt].add(src)

    visited = set()
    subgraphs = []

    # Sort keys for deterministic order
    node_ids = sorted(list(nodes_map.keys()))

    for start_node in node_ids:
        if start_node in visited:
            continue

        # BFS to find component
        component_ids = set()
        queue = [start_node]
        visited.add(start_node)
        component_ids.add(start_node)

        while queue:
            curr = queue.pop(0)
            for neighbor in adjacency.get(curr, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    component_ids.add(neighbor)
                    queue.append(neighbor)

        # Collect nodes and edges for this component
        sub_nodes = [nodes_map[nid] for nid in component_ids]
        sub_edges = [
            e for e in graph_data['edges']
            if e['source'] in component_ids and e['target'] in component_ids
        ]

        subgraphs.append({"nodes": sub_nodes, "edges": sub_edges})

    # Sort subgraphs by size (node count) descending
    subgraphs.sort(key=lambda g: len(g['nodes']), reverse=True)
    return subgraphs


def compress_subgraph_sources(subgraph: dict) -> dict:
    """
    Groups all 'source' nodes in the subgraph under a single 'Web Resources' proxy node.
    - Original edges satisfying (Any -> Source) become (Any -> Proxy)
    - New edges added (Proxy -> Source)
    """
    new_nodes = []
    source_nodes = []

    # Separate source nodes from others
    for node in subgraph['nodes']:
        if node.get('type') == 'source':
            source_nodes.append(node)
        else:
            new_nodes.append(node)

    # If fewer than 2 sources, simplify: don't compress (or do we always want to?)
    # User said "clumb all the webs together". Even 1 source could benefit from being under a "Resources" folder if we want consistency,
    # but strictly speaking 1 source doesn't need clustering.
    # Let's stick to >= 2 to avoid creating a folder for a single item unless requested.
    if len(source_nodes) < 2:
        return subgraph

    # Create Proxy Node
    # Unique per subgraph visualization since they are isolated files
    proxy_id = "proxy_web_resources"
    proxy_node = {
        "id": proxy_id,
        "type": "proxy",
        "content": "Web Resources",
        "description": "Grouped collection of all web sources linked in this graph."
    }

    new_nodes.append(proxy_node)
    # Keep sources in the list so they are still visible when expanding connected to proxy
    new_nodes.extend(source_nodes)

    new_edges = []
    source_ids = {n['id'] for n in source_nodes}

    # Process existing edges
    # Connect Keywords/etc -> Proxy instead of -> Source
    seen_proxy_edge_sources = set()

    for edge in subgraph['edges']:
        if edge['target'] in source_ids:
            # Reroute to proxy
            # Avoid duplicate edges from same source to proxy
            if edge['source'] not in seen_proxy_edge_sources:
                new_edges.append({
                    "source": edge['source'],
                    "target": proxy_id,
                    "relation": "references_resources"
                })
                seen_proxy_edge_sources.add(edge['source'])
            # We DROP the direct link to the specific source from the keyword
        else:
            # Keep other edges as is
            new_edges.append(edge)

    # Add connections from Proxy -> Sources
    for src_node in source_nodes:
        new_edges.append({
            "source": proxy_id,
            "target": src_node['id'],
            "relation": "contains"
        })

    return {"nodes": new_nodes, "edges": new_edges}


def create_pyvis_network(graph_data: dict, output_path: str):
    """Create a PyVis HTML for a single subgraph."""
    try:
        from pyvis.network import Network
    except ImportError:
        print("Installing pyvis...")
        os.system("pip install pyvis -q")
        from pyvis.network import Network

    # Determine height based on node count
    net_height = "600px"

    net = Network(height=net_height, width="100%",
                  bgcolor="#0b0c10", font_color="#c5c6c7", directed=True)

    # Configuration for FontAwesome icons
    type_config = {
        "answer": {"color": "#66fcf1", "icon": "f0eb", "size": 50, "label_color": "#ffffff"},
        "keyword": {"color": "#f1c40f", "icon": "f02b", "size": 35, "label_color": "#f1c40f"},
        "source": {"color": "#1f2833", "icon": "f0c1", "size": 30, "label_color": "#888888"},
        "document": {"color": "#2c3e50", "icon": "f15b", "size": 25, "label_color": "#888888"},
        "topic": {"color": "#c5c6c7", "icon": "f0c2", "size": 30, "label_color": "#c5c6c7"},
        "question": {"color": "#45a29e", "icon": "f059", "size": 40, "label_color": "#c5c6c7"},
        # Folder icon
        "proxy": {"color": "#e74c3c", "icon": "f07b", "size": 45, "label_color": "#ffffff"}
    }

    seen_ids = set()
    for node in graph_data["nodes"]:
        n_id = node["id"]
        if n_id in seen_ids:
            continue
        seen_ids.add(n_id)

        n_type = node.get("type", "topic")
        config = type_config.get(n_type, type_config["topic"])
        content = node.get("content", node.get("url", ""))

        import textwrap
        wrapped_content = "\\n".join(textwrap.wrap(content, width=50))
        tooltip_text = f"[{n_type.upper()}]\\n{'-'*20}\\n{wrapped_content}"

        label_text = content
        if len(label_text) > 25:
            label_text = label_text[:22] + "..."

        net.add_node(
            n_id,
            label=label_text,
            title=tooltip_text,
            shape='icon',
            icon={
                'face': "'FontAwesome'",
                'code': chr(int(config['icon'], 16)),
                'size': config['size'],
                'color': config['color']
            },
            font={'color': config['label_color'], 'face': 'arial',
                  'size': 16, 'strokeWidth': 2, 'strokeColor': "#000000"}
        )

    for edge in graph_data["edges"]:
        relation = edge.get("relation", "related")
        color = "#2b3543"
        width = 1
        dashes = False
        font_color = "#888888"

        if relation in ["required_for", "enables"]:
            color = "#66fcf1"
            width = 3
            font_color = "#66fcf1"
        elif relation in ["subset_of", "part_of"]:
            color = "#45a29e"
            width = 2
            dashes = True
            font_color = "#45a29e"
        elif relation == "source_for":
            color = "#2c3e50"
            width = 1
        elif relation == "references_resources":
            color = "#e74c3c"
            width = 2
            font_color = "#e74c3c"
        elif relation == "contains":
            color = "#555555"
            width = 1
            dashes = True

        net.add_edge(
            edge["source"], edge["target"],
            label=relation, title=relation, color=color, width=width,
            arrows={'to': {'enabled': True, 'scaleFactor': 0.5}},
            dashes=dashes,
            font={'color': font_color, 'size': 12, 'align': 'middle',
                  'background': '#0b0c10', 'strokeWidth': 0},
            smooth={'type': 'cubicBezier', 'roundness': 0.5}
        )

    options = {
        "nodes": {"font": {"strokeWidth": 2, "strokeColor": "#0b0c10"}},
        "edges": {"color": {"inherit": False}, "smooth": {"enabled": True, "type": "cubicBezier", "forceDirection": "vertical", "roundness": 0.5}},
        "layout": {
            "hierarchical": {
                "enabled": True, "direction": "UD", "sortMethod": "directed",
                "nodeSpacing": 200, "levelSeparation": 150, "treeSpacing": 220,
                "blockShifting": True, "edgeMinimization": True, "parentCentralization": True
            }
        },
        "physics": {
            "hierarchicalRepulsion": {"centralGravity": 0.0, "springLength": 100, "springConstant": 0.01, "nodeDistance": 220, "damping": 0.09},
            "solver": "hierarchicalRepulsion",
            "stabilization": {"enabled": True, "iterations": 1000}
        }
    }
    net.set_options(json.dumps(options))
    net.save_graph(output_path)

    # Inject Custom CSS and FontAwesome
    with open(output_path, 'r') as f:
        html_content = f.read()

    fa_link = '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">'
    if "font-awesome" not in html_content:
        html_content = html_content.replace(
            '<head>', f'<head>\\n    {fa_link}')

    custom_css = """
    <style>
        body { background-color: #0b0c10 !important; margin: 0; padding: 0; overflow: hidden; }
        div.vis-tooltip {
            background-color: #1f2833 !important;
            border: 1px solid #66fcf1 !important;
            color: #c5c6c7 !important;
            font-family: monospace !important;
            font-size: 14px !important;
            border-radius: 4px !important;
            padding: 10px !important;
            box-shadow: 0 0 10px rgba(102, 252, 241, 0.2) !important;
            white-space: pre-wrap !important; 
            max-width: 400px !important;
            z-index: 10000; 
        }
        .vis-configuration-wrapper { display: none; }
    </style>
    """
    html_content = html_content.replace('</head>', f'{custom_css}\\n</head>')

    with open(output_path, 'w') as f:
        f.write(html_content)


def create_master_visualization(subgraphs: List[dict], output_base_name: str, output_dir: str):
    """Create a master HTML file stacking iframes of subgraphs."""
    parts_dir = os.path.join(output_dir, "parts")
    if os.path.exists(parts_dir):
        shutil.rmtree(parts_dir)
    os.makedirs(parts_dir)

    part_files = []

    print(f"Generating visualizations for {len(subgraphs)} subgraphs...")

    for i, subgraph in enumerate(subgraphs):
        # Apply proxy compression here
        compressed_subgraph = compress_subgraph_sources(subgraph)

        part_filename = f"{output_base_name}_part_{i+1}.html"
        part_path = os.path.join(parts_dir, part_filename)
        create_pyvis_network(compressed_subgraph, part_path)
        part_files.append(f"parts/{part_filename}")
        print(
            f"  - Generated subgraph {i+1} ({len(compressed_subgraph['nodes'])} nodes)")

    # Create Master HTML
    master_path = os.path.join(output_dir, f"{output_base_name}.html")

    iframe_blocks = ""
    for part_ref in part_files:
        iframe_blocks += f"""
        <div class="graph-container">
            <iframe src="{part_ref}" scrolling="no"></iframe>
        </div>
        """

    master_html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Knowledge Graph Visualization</title>
    <style>
        body {{
            background-color: #0b0c10;
            color: #c5c6c7;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
        }}
        h1 {{
            text-align: center;
            color: #66fcf1;
            margin-bottom: 30px;
        }}
        .graph-container {{
            width: 100%;
            height: 650px;
            margin-bottom: 40px;
            border: 1px solid #1f2833;
            border-radius: 8px;
            overflow: hidden;
            background-color: #0b0c10;
            box-shadow: 0 4px 15px rgba(0,0,0,0.5);
        }}
        iframe {{
            width: 100%;
            height: 100%;
            border: none;
        }}
    </style>
</head>
<body>
    <h1>Knowledge Graphs ({len(subgraphs)} Sessions)</h1>
    {iframe_blocks}
</body>
</html>
    """

    with open(master_path, 'w') as f:
        f.write(master_html)

    return master_path

import html
import tempfile

def generate_stacked_graph_html(graph_data: dict) -> str:
    """Generate a single HTML string containing stacked PyVis graphs."""
    if not graph_data or not graph_data.get("nodes"):
        return "<html><body style='background-color:#0A0C10;'><h3 style='color:#c5c6c7;text-align:center;margin-top:50px;font-family:sans-serif;'>No graph data available.</h3></body></html>"

    subgraphs = get_connected_subgraphs(graph_data)
    iframe_blocks = ""

    for i, subgraph in enumerate(subgraphs):
        compressed = compress_subgraph_sources(subgraph)
        
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tmp:
            tmp_path = tmp.name
        
        create_pyvis_network(compressed, tmp_path)
        
        with open(tmp_path, 'r') as f:
            part_html = f.read()
            
        os.remove(tmp_path)
        
        # Escape the HTML for srcdoc
        escaped_html = html.escape(part_html)
        
        iframe_blocks += f"""
        <div class="graph-container">
            <iframe srcdoc="{escaped_html}" scrolling="no"></iframe>
        </div>
        """

    master_html = f"""<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            background-color: #0A0C10;
            color: #c5c6c7;
            font-family: 'DM Sans', sans-serif;
            margin: 0;
            padding: 20px;
        }}
        h1 {{
            text-align: center;
            color: #705CFF;
            margin-bottom: 30px;
            font-size: 1.5rem;
            letter-spacing: 0.05em;
        }}
        .graph-container {{
            width: 100%;
            height: 650px;
            margin-bottom: 40px;
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            overflow: hidden;
            background-color: #0b0c10;
            box-shadow: 0 8px 32px rgba(0,0,0,0.4);
        }}
        iframe {{
            width: 100%;
            height: 100%;
            border: none;
        }}
    </style>
</head>
<body>
    <h1>Knowledge Graph Map ({len(subgraphs)} Stages)</h1>
    {iframe_blocks}
</body>
</html>
    """
    return master_html


def main():
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
    else:
        files = glob.glob("log/knowledge_map_*.json")
        if files:
            files.sort(key=lambda f: int(
                f.replace("log/knowledge_map_", "").replace(".json", "")))
            filepath = files[-1]
        else:
            filepath = "log/knowledge_map.json"

    if not os.path.exists(filepath):
        print(f"Error: {filepath} not found.")
        sys.exit(1)

    print(f"Processing: {filepath}")
    graph_data = load_graph(filepath)

    if len(graph_data.get("nodes", [])) == 0:
        print("Graph is empty.")
        return

    subgraphs = get_connected_subgraphs(graph_data)

    output_dir = os.path.dirname(filepath)
    output_base = "knowledge_graph_" + \
        os.path.basename(filepath).replace(".json", "")

    master_path = create_master_visualization(
        subgraphs, output_base, output_dir)

    print(f"Visualization saved to: {master_path}")
    import webbrowser
    webbrowser.open(f"file://{os.path.abspath(master_path)}")


if __name__ == "__main__":
    main()

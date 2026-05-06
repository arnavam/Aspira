import asyncio
import os
import webbrowser
from database import Database
from visualize_graph import generate_stacked_graph_html

async def test_visualization():
    # Uses your project's Database class (no motor needed)
    db = Database()
    
    # 1. Fetch the latest knowledge graph from DB
    print("Fetching latest knowledge graph from MongoDB...")
    # We query the collection directly since Database doesn't have a 'get latest' helper yet
    latest_graph_doc = await db.db.knowledge_graphs.find_one(sort=[("updated_at", -1)])
    
    if not latest_graph_doc:
        print("No knowledge graph found in database. Please run an interview first!")
        return

    graph_data = latest_graph_doc.get("graph_data", {})
    conv_id = latest_graph_doc.get("conversation_id", "unknown")
    print(f"Found graph for session: {conv_id}")

    # 2. Generate the stacked HTML using the refactored visualize_graph logic
    print("Generating stacked PyVis visualization...")
    html_content = generate_stacked_graph_html(graph_data)

    # 3. Save to a temporary file and open it
    output_file = "test_output.html"
    with open(output_file, "w") as f:
        f.write(html_content)
    
    full_path = os.path.abspath(output_file)
    print(f"\nSuccess! Visualization saved to: {full_path}")
    print("Opening in browser...")
    webbrowser.open(f"file://{full_path}")

if __name__ == "__main__":
    asyncio.run(test_visualization())

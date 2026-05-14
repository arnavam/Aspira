import pytest
from database import Database

@pytest.mark.asyncio
async def test_knowledge_graph_save_and_get(test_db: Database):
    user_id = "user_123"
    conv_id = "conv_1"
    
    kg_data = {
        "nodes": [{"id": "Python", "label": "Python", "group": "skill"}],
        "links": [{"source": "Python", "target": "API", "label": "used for"}]
    }
    
    await test_db.save_knowledge_graph(user_id, conv_id, kg_data)
    
    retrieved = await test_db.get_knowledge_graph(user_id, conv_id)
    assert retrieved is not None
    assert "nodes" in retrieved
    assert retrieved["nodes"][0]["id"] == "Python"

import pandas as pd

def search_onet_data(job_title, knowledge_file, skills_file, abilities_file):

    
    # Load all three Excel files
    try:
        knowledge_df = pd.read_excel(knowledge_file)
        skills_df = pd.read_excel(skills_file)
        abilities_df = pd.read_excel(abilities_file)
    except Exception as e:
        return {"error": f"Failed to load Excel files: {str(e)}"}
    
    # Initialize result dictionary
    results = {
        "job_title": job_title,
        "knowledge": [],
        "skills": [],
        "abilities": []
    }
    
    # Search in Knowledge file
    if "Title" in knowledge_df.columns:
        knowledge_results = knowledge_df[knowledge_df["Title"].str.contains(job_title, case=False, na=False)]
        results["knowledge"] = knowledge_results.to_dict('records')
    
    # Search in Skills file
    if "Title" in skills_df.columns:
        skills_results = skills_df[skills_df["Title"].str.contains(job_title, case=False, na=False)]
        results["skills"] = skills_results.to_dict('records')
    
    # Search in Abilities file
    if "Title" in abilities_df.columns:
        abilities_results = abilities_df[abilities_df["Title"].str.contains(job_title, case=False, na=False)]
        results["abilities"] = abilities_results.to_dict('records')
    
    return results

# Example usage
if __name__ == "__main__":
    # Replace these with your actual file paths
    knowledge_path = "file/Knowledge.xlsx"
    skills_path = "file/Skills.xlsx"
    abilities_path = "file/Abilities.xlsx"
    
    job_to_search ="Chartered accountant"
    
    results = search_onet_data(job_to_search, knowledge_path, skills_path, abilities_path)
    
    # Print results in a readable format
    print(f"\nResults for '{job_to_search}':")
    # print(results)
    print("\nKnowledge:")
    for item in results["knowledge"]:
        print(f"- {item.get('Element Name', 'N/A')}: {item.get('Description', 'No description')}")
    
    print("\nSkills:")
    for item in results["skills"]:
        print(f"- {item.get('Element Name', 'N/A')}: {item.get('Description', 'No description')}")
    
    print("\nAbilities:")
    for item in results["abilities"]:
        print(f"- {item.get('Element Name', 'N/A')}: {item.get('Description', 'No description')}")
    
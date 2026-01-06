
import yaml
import json
import sqlparse
from app import (
    load_recipes,
    get_report_structure_with_llm,
    get_sql_from_recipe,
)
from core.sql_template_engine import SQLTemplateEngine

def main():
    """
    Runs an end-to-end test for the report generation process based on a specific user query.
    """
    # 1. Define the user query for the test
    user_query = "30대 당뇨병 환자 리포트"
    print(f"🚀 Starting report generation for query: \"{user_query}\"")
    print("-" * 50)

    # 2. Initialize SQL Template Engine
    template_engine = SQLTemplateEngine()

    # 3. Load all available recipes
    all_recipes = load_recipes()
    if not all_recipes:
        print("❌ No recipes found. Exiting.")
        return

    recipe_dict = {recipe['name']: recipe for recipe in all_recipes if recipe}
    print(f"✅ {len(all_recipes)} recipes loaded successfully.")
    print("-" * 50)

    # 3. Call the LLM to get the report structure
    print("🧠 Calling LLM to generate report structure... (This may take a moment)")
    report_structure = get_report_structure_with_llm(user_query, all_recipes)

    if not report_structure:
        print("❌ Failed to get a valid report structure from the LLM.")
        return

    print("✅ LLM returned a report structure.")
    print("-" * 50)

    # 4. Print the high-level report information
    print(f"📄 REPORT TITLE: {report_structure.get('report_title')}")
    print("\n** EXECUTIVE SUMMARY **")
    print(report_structure.get('executive_summary', 'N/A'))
    print("\n** TABLE OF CONTENTS **")
    for item in report_structure.get('table_of_contents', []):
        print(f"- {item}")
    print("-" * 50)

    # 5. Process and print each page of the report
    if "pages" in report_structure:
        for i, page in enumerate(report_structure["pages"]):
            print(f"\n📑 PAGE {i+1}: {page.get('title')}")
            print(f"   Rationale: {page.get('rationale')}")
            print(f"   Recipe Used: {page.get('recipe_name')}")
            print(f"   Parameters Found: {json.dumps(page.get('parameters', {}), indent=2, ensure_ascii=False)}")

            recipe_name = page.get("recipe_name")
            recipe = recipe_dict.get(recipe_name)
            llm_params = page.get("parameters", {})

            if not recipe:
                print(f"   🚨 ERROR: Recipe '{recipe_name}' not found in loaded recipes.")
                continue

            # Generate and print the final SQL
            sql_template = get_sql_from_recipe(recipe)
            final_sql = template_engine.render(sql_template, llm_params)
            
            print("\n   --- FINAL SQL ---")
            print(final_sql)
            print("   -----------------")

            # Validate the SQL syntax
            try:
                parsed = sqlparse.parse(final_sql)
                if not parsed:
                    raise ValueError("SQL could not be parsed.")
                
                has_error = any(
                    t.ttype is sqlparse.tokens.Error for statement in parsed for t in statement.flatten()
                )

                if has_error:
                    print("   ✅ SQL Syntax Validation: ⚠️  Potential syntax error detected by sqlparse.")
                else:
                    print("   ✅ SQL Syntax Validation: OK")

            except Exception as e:
                print(f"   🚨 SQL Syntax Validation: FAILED ({e})")

            print("-" * 50)

if __name__ == "__main__":
    main()

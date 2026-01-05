
import os
import yaml
import glob
from core.sql_template_engine import SQLTemplateEngine

def generate_dummy_parameters(recipe_params):
    """Generates a dictionary of dummy parameters based on the recipe's YAML definition."""
    dummy_params = {}
    for param in recipe_params:
        param_name = param.get("name")
        param_type = param.get("type")
        default_value = param.get("default")

        if default_value is not None:
            dummy_params[param_name] = default_value
            continue

        # Assign dummy values based on type or name for required params
        if "date" in param_type:
            if "start" in param_name:
                dummy_params[param_name] = "2022-01-01"
            else:
                dummy_params[param_name] = "2024-12-31"
        elif "integer" in param_type:
            if "age" in param_name:
                dummy_params[param_name] = 35
            else:
                dummy_params[param_name] = 10
        elif "string" in param_type:
            if param_name == "drug1_ingredient":
                dummy_params[param_name] = "아스피린"
            elif param_name == "drug2_ingredient":
                dummy_params[param_name] = "이부프로펜"
            elif param_name == "from_disease_keyword":
                dummy_params[param_name] = "지방간"
            elif param_name == "to_disease_keyword":
                dummy_params[param_name] = "염증성 간질환"
            elif param_name == "target_ingredient":
                dummy_params[param_name] = "아스피린" # A common drug ingredient
            elif "keyword" in param_name:
                dummy_params[param_name] = "당뇨병" # A common test keyword
            else:
                dummy_params[param_name] = "test_string"
        else: # fallback for other types
            dummy_params[param_name] = "dummy_value"
            
    # A specific override that is often needed but not always defined with a default
    if 'snapshot_dt' not in dummy_params:
        dummy_params['snapshot_dt'] = '2025-09-01'

    return dummy_params

def main():
    """
    Generates executable SQL files for all recipes by filling them with dummy parameters.
    """
    recipe_dir = "recipes"
    output_dir = "generated_sql_for_testing"

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Initialize SQL Template Engine
    template_engine = SQLTemplateEngine(recipes_dir=recipe_dir)

    # Find all recipe.yaml files
    recipe_yaml_files = glob.glob(os.path.join(recipe_dir, "**", "*.yaml"), recursive=True)

    print(f"Found {len(recipe_yaml_files)} recipes. Generating SQL for each...")

    generated_count = 0
    error_count = 0

    for yaml_path in recipe_yaml_files:
        try:
            with open(yaml_path, "r", encoding="utf-8") as f:
                recipe = yaml.safe_load(f)

            if not recipe or 'name' not in recipe or 'parameters' not in recipe:
                print(f"- Skipping invalid or incomplete recipe: {yaml_path}")
                continue

            # Associate the SQL file path
            sql_file_path = yaml_path.replace(".yaml", ".sql")
            if not os.path.exists(sql_file_path):
                 # Handle .bak files by trying to find the original
                if yaml_path.endswith('.yaml.bak'):
                    original_sql_path = yaml_path.replace(".yaml.bak", ".sql")
                    if os.path.exists(original_sql_path):
                         sql_file_path = original_sql_path
                    else:
                        print(f"- Skipping .bak recipe, original .sql not found: {yaml_path}")
                        continue
                else:
                    print(f"- Skipping, SQL file not found for: {yaml_path}")
                    continue

            # Generate dummy parameters
            dummy_params = generate_dummy_parameters(recipe["parameters"])

            # Load SQL template and render with parameters
            with open(sql_file_path, 'r', encoding='utf-8') as f:
                sql_template = f.read()
            final_sql = template_engine.render(sql_template, dummy_params)
            
            # Save the generated SQL to a file
            output_filename = f"{recipe['name']}.sql"
            output_path = os.path.join(output_dir, output_filename)
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(f"-- Generated from: {os.path.basename(yaml_path)}\n")
                f.write(f"-- Parameters used: {dummy_params}\n\n")
                f.write(final_sql)
            
            generated_count += 1
            print(f"  - Successfully generated: {output_filename}")

        except Exception as e:
            print(f"  - 🚨 Error processing {os.path.basename(yaml_path)}: {e}")
            error_count += 1
            
    print("-" * 50)
    print(f"✅ Generation complete.")
    print(f"   Total files generated: {generated_count}")
    print(f"   Total errors: {error_count}")
    print(f"   Generated SQL files are located in the '{output_dir}' directory.")

if __name__ == "__main__":
    main()

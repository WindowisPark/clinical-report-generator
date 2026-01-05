import os
import json
import argparse
import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph

# Core imports
from core.recipe_loader import RecipeLoader
from core.sql_template_engine import SQLTemplateEngine
from services.gemini_service import GeminiService
from services.databricks_client import DatabricksClient

# Font Configuration
FONT_NAME = 'NanumGothic'
FONT_PATH = os.path.abspath('NanumGothic.ttf')

def setup_fonts():
    """Register Korean font for ReportLab and Matplotlib"""
    # ReportLab
    if os.path.exists(FONT_PATH):
        pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_PATH))
        print(f"✅ Registered font: {FONT_NAME}")
    else:
        print(f"⚠️ Font file not found: {FONT_PATH}. Korean characters may not render correctly.")

    # Matplotlib
    if os.path.exists(FONT_PATH):
        import matplotlib.font_manager as fm
        fe = fm.FontEntry(
            fname=FONT_PATH,
            name=FONT_NAME
        )
        fm.fontManager.ttflist.insert(0, fe)
        # We will set rcParams in create_chart to override seaborn defaults
        print(f"✅ Configured Matplotlib font: {FONT_NAME}")

def load_prompts():
    base_path = "prompts/report_generation"
    with open(os.path.join(base_path, "system.txt"), "r") as f:
        system_prompt = f.read()
    with open(os.path.join(base_path, "user_template.txt"), "r") as f:
        user_template = f.read()
    return system_prompt, user_template

def get_report_structure_with_llm(query, all_recipes):
    system_prompt, user_template = load_prompts()
    
    # Format recipe list for prompt
    recipe_list_str = ""
    for recipe in all_recipes:
        recipe_list_str += f"- Name: {recipe['name']}\n"
        recipe_list_str += f"  Description: {recipe.get('description', 'N/A')}\n"
        recipe_list_str += f"  Parameters: {json.dumps(recipe.get('parameters', []), ensure_ascii=False)}\n\n"
        
    # Fill template
    prompt = user_template.replace("{{USER_QUERY}}", query)
    prompt = prompt.replace("{{RECIPE_LIST}}", recipe_list_str)
    prompt = prompt.replace("{{MANDATORY_RECIPES_SECTION}}", "") # Optional
    prompt = prompt.replace("{{DATABRICKS_RULES}}", "") # Optional, could load from file
    prompt = prompt.replace("{{SCHEMA_INFO}}", "") # Optional
    prompt = prompt.replace("{{OUTPUT_VALIDATION}}", "") # Optional
    prompt = prompt.replace("{{EXAMPLES}}", "") # Optional
    
    full_prompt = f"{system_prompt}\n\n{prompt}"
    
    print("🤖 Calling Gemini to generate report structure...")
    gemini = GeminiService()
    response = gemini.generate_content(full_prompt)
    
    try:
        text = response.text
        # Clean up markdown code blocks if present
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        return json.loads(text)
    except Exception as e:
        print(f"❌ Failed to parse LLM response: {e}")
        print(f"Response text: {response.text}")
        return None

def generate_chart_insight(df, report_title, chart_title, recipe_name):
    """
    Generate a concise insight for the chart using Gemini.
    """
    if df.empty:
        return "데이터가 없어 분석할 수 없습니다."
        
    # Prepare data summary
    summary_str = f"Columns: {', '.join(df.columns)}\n"
    summary_str += f"Row Count: {len(df)}\n"
    summary_str += "Top 10 Rows:\n"
    summary_str += df.head(10).to_string(index=False)
    
    # Load prompt
    prompt_path = "prompts/report_generation/chart_insight.txt"
    try:
        with open(prompt_path, "r") as f:
            prompt_template = f.read()
    except FileNotFoundError:
        print(f"⚠️ Prompt file not found: {prompt_path}")
        return "인사이트 생성 실패 (프롬프트 없음)"
        
    # Fill prompt
    prompt = prompt_template.replace("{{REPORT_TITLE}}", report_title)
    prompt = prompt.replace("{{CHART_TITLE}}", chart_title)
    prompt = prompt.replace("{{RECIPE_NAME}}", recipe_name)
    prompt = prompt.replace("{{DATA_SUMMARY}}", summary_str)
    
    print(f"🤖 Generating insight for chart: {chart_title}...")
    gemini = GeminiService()
    try:
        response = gemini.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"❌ Failed to generate insight: {e}")
        return "인사이트 생성 중 오류가 발생했습니다."

def create_chart(df, chart_type, title, output_path):
    plt.figure(figsize=(10, 6))
    sns.set_theme(style="whitegrid")
    
    # Override font AFTER seaborn theme
    if os.path.exists(FONT_PATH):
        plt.rcParams['font.family'] = FONT_NAME
        plt.rcParams['axes.unicode_minus'] = False
    
    if df.empty:
        plt.text(0.5, 0.5, 'No Data Available', ha='center', va='center')
    else:
        try:
            # Heuristic: First column is category, last column is value (usually count)
            # Or try to find numeric columns
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                y_col = numeric_cols[0]
                # Find a non-numeric column for x, or use index
                non_numeric = df.select_dtypes(exclude=['number']).columns
                if len(non_numeric) > 0:
                    x_col = non_numeric[0]
                else:
                    x_col = df.index.name if df.index.name else 'index'
                    df = df.reset_index()
            else:
                # Fallback
                x_col = df.columns[0]
                y_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]

            if chart_type == 'bar':
                sns.barplot(x=x_col, y=y_col, data=df, palette="viridis")
            elif chart_type == 'pie':
                plt.pie(df[y_col], labels=df[x_col], autopct='%1.1f%%')
            elif chart_type == 'line':
                sns.lineplot(x=x_col, y=y_col, data=df, marker='o')
            else:
                sns.barplot(x=x_col, y=y_col, data=df, palette="viridis")
                
            plt.title(title)
            plt.xticks(rotation=45)
            plt.tight_layout()
        except Exception as e:
            print(f"⚠️ Error creating chart: {e}")
            plt.text(0.5, 0.5, f'Chart Error: {e}', ha='center', va='center')

    plt.savefig(output_path)
    plt.close()

def draw_cover_page(c, width, height, report_title, query):
    """Draws a professional fixed cover page."""
    # Background Color (Optional, keeping it white for printability but adding a header strip)
    # Header Strip
    c.setFillColor(HexColor('#2C3E50')) # Dark Blue
    c.rect(0, height - 100, width, 100, fill=1, stroke=0)
    
    # Header Text
    c.setFillColor(HexColor('#FFFFFF'))
    c.setFont(FONT_NAME if os.path.exists(FONT_PATH) else "Helvetica-Bold", 24)
    c.drawCentredString(width / 2, height - 60, "CLINICAL INSIGHT REPORT")
    
    # Reset Color
    c.setFillColor(HexColor('#000000'))
    
    # Report Title
    c.setFont(FONT_NAME if os.path.exists(FONT_PATH) else "Helvetica-Bold", 32)
    # Simple wrapping for title if too long
    if c.stringWidth(report_title) > width - 100:
        c.setFont(FONT_NAME if os.path.exists(FONT_PATH) else "Helvetica-Bold", 24)
    c.drawCentredString(width / 2, height / 2 + 50, report_title)
    
    # Divider Line
    c.setLineWidth(2)
    c.setStrokeColor(HexColor('#2C3E50'))
    c.line(100, height / 2, width - 100, height / 2)
    
    # Metadata
    c.setFont(FONT_NAME if os.path.exists(FONT_PATH) else "Helvetica", 14)
    c.drawCentredString(width / 2, height / 2 - 40, f"Query: {query}")
    c.drawCentredString(width / 2, height / 2 - 70, f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d')}")
    
    # Footer
    c.setFont(FONT_NAME if os.path.exists(FONT_PATH) else "Helvetica-Oblique", 10)
    c.setFillColor(HexColor('#7F8C8D')) # Grey
    c.drawCentredString(width / 2, 50, "Confidential - Internal Use Only")
    
    c.showPage()

def generate_pdf(report_structure, query, output_filename):
    setup_fonts()
    c = canvas.Canvas(output_filename, pagesize=A4)
    width, height = A4
    
    # 1. Cover Page
    draw_cover_page(c, width, height, report_structure.get('report_title', 'Clinical Report'), query)
    
    # 2. Executive Summary (Page 2)
    c.setFont(FONT_NAME if os.path.exists(FONT_PATH) else "Helvetica-Bold", 20)
    c.drawString(50, height - 80, "Executive Summary")
    
    # Divider
    c.setLineWidth(1)
    c.setStrokeColor(HexColor('#CCCCCC'))
    c.line(50, height - 95, width - 50, height - 95)
    
    c.setFont(FONT_NAME if os.path.exists(FONT_PATH) else "Helvetica", 12)
    c.setFillColor(HexColor('#000000'))
    
    text_object = c.beginText(50, height - 120)
    text_object.setFont(FONT_NAME if os.path.exists(FONT_PATH) else "Helvetica", 12)
    text_object.setLeading(18) # Line spacing
    
    summary = report_structure.get('executive_summary', 'No summary provided.')
    
    # Basic text wrapping
    words = summary.split()
    line = ""
    for word in words:
        if c.stringWidth(line + " " + word) < 480:
            line += " " + word
        else:
            text_object.textLine(line)
            line = word
    text_object.textLine(line)
    c.drawText(text_object)
    
    c.showPage()
    
    # Initialize services
    client = DatabricksClient()
    template_engine = SQLTemplateEngine()
    recipe_loader = RecipeLoader()
    
    if "pages" in report_structure:
        for i, page in enumerate(report_structure["pages"]):
            title = page.get('title', f'Page {i+1}')
            recipe_name = page.get('recipe_name')
            llm_params = page.get('parameters', {})
            rationale = page.get('rationale', '')
            
            print(f"📄 Processing page {i+1}: {title} ({recipe_name})")
            
            # Header
            c.setFont(FONT_NAME if os.path.exists(FONT_PATH) else "Helvetica-Bold", 18)
            c.drawString(50, height - 50, title)
            
            c.setFont(FONT_NAME if os.path.exists(FONT_PATH) else "Helvetica-Oblique", 10)
            c.drawString(50, height - 70, f"Rationale: {rationale}")
            
            # Execute Recipe
            recipe = recipe_loader.get_recipe_by_name(recipe_name)
            if recipe:
                try:
                    # Render SQL
                    final_sql = template_engine.render_template(recipe_name, llm_params)
                    print(f"   Executing SQL...")
                    
                    # Execute SQL
                    result = client.execute_query(final_sql)
                    
                    if result['success']:
                        df = result['data']
                        print(f"   ✅ Query returned {len(df)} rows.")
                        
                        # Generate Chart
                        chart_filename = f"temp_chart_{i}.png"
                        # Determine chart type from recipe visualization metadata or default
                        viz_type = recipe.get('visualization', {}).get('type', 'bar')
                        create_chart(df, viz_type, title, chart_filename)
                        
                        # Draw Chart
                        try:
                            c.drawImage(chart_filename, 50, height - 400, width=500, height=300)
                            os.remove(chart_filename)
                        except Exception as e:
                            print(f"   ⚠️ Failed to draw image: {e}")
                        
                        # Generate and Draw Insight
                        insight = generate_chart_insight(df, report_structure.get('report_title', 'Report'), title, recipe_name)
                        
                        # Draw Insight Box
                        c.setFillColor(HexColor('#F0F0F0'))
                        c.rect(50, height - 520, 500, 100, fill=1, stroke=0)
                        c.setFillColor(HexColor('#000000'))
                        
                        c.setFont(FONT_NAME if os.path.exists(FONT_PATH) else "Helvetica-Bold", 10)
                        c.drawString(60, height - 435, "💡 AI Insight")
                        
                        # Text wrapping for insight
                        c.setFont(FONT_NAME if os.path.exists(FONT_PATH) else "Helvetica", 9)
                        text_object = c.beginText(60, height - 450)
                        text_object.setFont(FONT_NAME if os.path.exists(FONT_PATH) else "Helvetica", 9)
                        
                        words = insight.split()
                        line = ""
                        for word in words:
                            if c.stringWidth(line + " " + word) < 480:
                                line += " " + word
                            else:
                                text_object.textLine(line)
                                line = word
                        text_object.textLine(line)
                        c.drawText(text_object)

                        # Draw Table (Top 5)
                        y_offset = height - 550
                        c.setFont(FONT_NAME if os.path.exists(FONT_PATH) else "Helvetica-Bold", 10)
                        c.drawString(50, y_offset, "Data Preview (Top 5 rows):")
                        y_offset -= 20
                        c.setFont(FONT_NAME if os.path.exists(FONT_PATH) else "Helvetica", 8)
                        
                        if not df.empty:
                            # Simple table drawing
                            cols = df.columns.tolist()
                            header = " | ".join(cols)
                            c.drawString(50, y_offset, header[:100]) # Truncate if too long
                            y_offset -= 15
                            
                            for idx, row in df.head(5).iterrows():
                                row_str = " | ".join([str(val) for val in row.values])
                                c.drawString(50, y_offset, row_str[:100])
                                y_offset -= 15
                    else:
                        c.setFont(FONT_NAME if os.path.exists(FONT_PATH) else "Helvetica", 10)
                        c.setFillColor(HexColor('#FF0000'))
                        c.drawString(50, height - 200, f"Error: {result['error_message']}")
                        c.setFillColor(HexColor('#000000'))
                        
                except Exception as e:
                    print(f"   ❌ Error processing recipe: {e}")
                    c.drawString(50, height - 200, f"Processing Error: {e}")
            else:
                print(f"   ❌ Recipe '{recipe_name}' not found.")
                c.drawString(50, height - 200, f"Recipe '{recipe_name}' not found.")
            
            c.showPage()
            
    c.save()
    print(f"✅ PDF Report saved to {output_filename}")

def main():
    parser = argparse.ArgumentParser(description='Generate a Clinical PDF Report.')
    parser.add_argument('--query', type=str, required=True, help='The natural language query for the report.')
    parser.add_argument('--output', type=str, default='output', help='Output directory.')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.output):
        os.makedirs(args.output)
        
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    output_filename = os.path.join(args.output, f"report_{timestamp}.pdf")
    
    print(f"🚀 Starting report generation for: \"{args.query}\"")
    
    # Load recipes
    recipe_loader = RecipeLoader()
    all_recipes = recipe_loader.get_all_recipes()
    print(f"📚 Loaded {len(all_recipes)} recipes.")

    # Get structure
    report_structure = get_report_structure_with_llm(args.query, all_recipes)
    
    if not report_structure:
        print("❌ Failed to generate report structure.")
        return
        
    print(f"📋 Report Title: {report_structure.get('report_title')}")
    
    # Generate PDF
    generate_pdf(report_structure, args.query, output_filename)

if __name__ == "__main__":
    main()

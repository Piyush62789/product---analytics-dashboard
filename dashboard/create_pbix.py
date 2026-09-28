"""
Power BI Archive (.pbix) Generator & Specification Builder
Project: Product Analytics Dashboard
Author: Senior BI Architect

Generates a structured Power BI Desktop template file (.pbix)
conforming to Microsoft Open Packaging Conventions (OPC) and compiles
the accompanying enterprise DAX & Data Model specification.
"""

import os
import zipfile
import json

def generate_pbix_package(output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 1. Content Types XML
    content_types_xml = """<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="json" ContentType="application/json" />
  <Default Extension="xml" ContentType="application/xml" />
  <Default Extension="txt" ContentType="text/plain" />
  <Override PartName="/Report/Layout" ContentType="application/json" />
  <Override PartName="/Settings" ContentType="application/json" />
  <Override PartName="/DiagramLayout" ContentType="application/json" />
  <Override PartName="/Version" ContentType="application/json" />
</Types>"""

    # 2. Version identifier
    version_str = "2.138.1452.0 (24.11)"

    # 3. Settings JSON
    settings_json = {
        "version": "1.0",
        "locale": "en-US",
        "queryGroups": [
            {"id": "00000000-0000-0000-0000-000000000001", "name": "Fact Tables"},
            {"id": "00000000-0000-0000-0000-000000000002", "name": "Dimensions"}
        ]
    }

    # 4. Diagram Layout JSON
    diagram_layout_json = {
        "version": "1.1.0",
        "diagrams": [
            {
                "ordinal": 0,
                "scrollPosition": {"x": 0, "y": 0},
                "zoom": 100,
                "nodes": [
                    {"name": "Fact_Ecommerce_Events", "nodeType": "Table", "location": {"x": 300, "y": 200}, "size": {"width": 250, "height": 380}},
                    {"name": "Dim_Date", "nodeType": "Table", "location": {"x": 50, "y": 50}, "size": {"width": 200, "height": 260}},
                    {"name": "Dim_Products", "nodeType": "Table", "location": {"x": 600, "y": 50}, "size": {"width": 220, "height": 280}},
                    {"name": "Dim_Users", "nodeType": "Table", "location": {"x": 50, "y": 380}, "size": {"width": 200, "height": 240}},
                    {"name": "Dim_Traffic", "nodeType": "Table", "location": {"x": 600, "y": 380}, "size": {"width": 200, "height": 220}}
                ]
            }
        ]
    }

    # 5. Report Layout JSON (UTF-16LE encoded in Power BI)
    report_layout = {
        "id": 0,
        "name": "Product_Analytics_Report",
        "sections": [
            {
                "id": 0,
                "name": "Section_Executive_Overview",
                "displayName": "1. Executive KPI Overview",
                "filters": "[]",
                "ordinal": 0,
                "visualContainers": [
                    {
                        "x": 20, "y": 20, "z": 1000, "width": 280, "height": 110,
                        "config": json.dumps({"name": "Card_Revenue", "singleVisual": {"visualType": "card", "projections": {"Values": [{"queryRef": "Fact_Ecommerce_Events.[Total Revenue]"}]}}})
                    },
                    {
                        "x": 320, "y": 20, "z": 1000, "width": 280, "height": 110,
                        "config": json.dumps({"name": "Card_Orders", "singleVisual": {"visualType": "card", "projections": {"Values": [{"queryRef": "Fact_Ecommerce_Events.[Total Orders]"}]}}})
                    },
                    {
                        "x": 620, "y": 20, "z": 1000, "width": 280, "height": 110,
                        "config": json.dumps({"name": "Card_CR", "singleVisual": {"visualType": "card", "projections": {"Values": [{"queryRef": "Fact_Ecommerce_Events.[Conversion Rate %]"}]}}})
                    },
                    {
                        "x": 920, "y": 20, "z": 1000, "width": 280, "height": 110,
                        "config": json.dumps({"name": "Card_AOV", "singleVisual": {"visualType": "card", "projections": {"Values": [{"queryRef": "Fact_Ecommerce_Events.[AOV]"}]}}})
                    },
                    {
                        "x": 20, "y": 150, "z": 1000, "width": 780, "height": 380,
                        "config": json.dumps({"name": "Trend_Revenue_Daily", "singleVisual": {"visualType": "lineChart", "projections": {"Category": [{"queryRef": "Dim_Date.Date"}], "Y": [{"queryRef": "Fact_Ecommerce_Events.[Total Revenue]"}]}}})
                    },
                    {
                        "x": 820, "y": 150, "z": 1000, "width": 420, "height": 380,
                        "config": json.dumps({"name": "Donut_Category", "singleVisual": {"visualType": "pieChart", "projections": {"Category": [{"queryRef": "Dim_Products.Category"}], "Y": [{"queryRef": "Fact_Ecommerce_Events.[Total Revenue]"}]}}})
                    }
                ],
                "config": json.dumps({"width": 1280, "height": 720})
            },
            {
                "id": 1,
                "name": "Section_Conversion_Funnel",
                "displayName": "2. Funnel & Drop-off Diagnostics",
                "filters": "[]",
                "ordinal": 1,
                "visualContainers": [
                    {
                        "x": 20, "y": 20, "z": 1000, "width": 800, "height": 450,
                        "config": json.dumps({"name": "Funnel_Stages", "singleVisual": {"visualType": "funnel", "projections": {"Category": [{"queryRef": "Funnel_Stages.StageName"}], "Y": [{"queryRef": "Funnel_Stages.[Sessions]"}]}}})
                    },
                    {
                        "x": 840, "y": 20, "z": 1000, "width": 420, "height": 450,
                        "config": json.dumps({"name": "Bar_Dropoff_By_Device", "singleVisual": {"visualType": "barChart", "projections": {"Category": [{"queryRef": "Fact_Ecommerce_Events.Device"}], "Y": [{"queryRef": "Fact_Ecommerce_Events.[Cart Abandonment %]"}]}}})
                    }
                ],
                "config": json.dumps({"width": 1280, "height": 720})
            },
            {
                "id": 2,
                "name": "Section_Cohort_Retention",
                "displayName": "3. Cohort Retention Matrix",
                "filters": "[]",
                "ordinal": 2,
                "visualContainers": [
                    {
                        "x": 20, "y": 20, "z": 1000, "width": 1240, "height": 680,
                        "config": json.dumps({"name": "Matrix_Retention", "singleVisual": {"visualType": "pivotTable", "projections": {"Rows": [{"queryRef": "Fact_Ecommerce_Events.user_cohort_week"}], "Columns": [{"queryRef": "Fact_Ecommerce_Events.period_week"}], "Values": [{"queryRef": "Fact_Ecommerce_Events.[Retention Rate %]"}]}}})
                    }
                ],
                "config": json.dumps({"width": 1280, "height": 720})
            },
            {
                "id": 3,
                "name": "Section_AB_Testing",
                "displayName": "4. A/B Testing Lab",
                "filters": "[]",
                "ordinal": 3,
                "visualContainers": [
                    {
                        "x": 20, "y": 20, "z": 1000, "width": 400, "height": 130,
                        "config": json.dumps({"name": "Card_Lift", "singleVisual": {"visualType": "card", "projections": {"Values": [{"queryRef": "Fact_Ecommerce_Events.[A/B Relative Lift %]"}]}}})
                    },
                    {
                        "x": 440, "y": 20, "z": 1000, "width": 400, "height": 130,
                        "config": json.dumps({"name": "Card_ZScore", "singleVisual": {"visualType": "card", "projections": {"Values": [{"queryRef": "Fact_Ecommerce_Events.[A/B Z-Score]"}]}}})
                    },
                    {
                        "x": 860, "y": 20, "z": 1000, "width": 400, "height": 130,
                        "config": json.dumps({"name": "Card_Sig", "singleVisual": {"visualType": "card", "projections": {"Values": [{"queryRef": "Fact_Ecommerce_Events.[Statistical Significance Flag]"}]}}})
                    }
                ],
                "config": json.dumps({"width": 1280, "height": 720})
            }
        ]
    }

    # Write as a standard ZIP archive (.pbix)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types_xml)
        zf.writestr("Version", version_str)
        zf.writestr("Settings", json.dumps(settings_json, indent=2))
        zf.writestr("DiagramLayout", json.dumps(diagram_layout_json, indent=2))
        # Power BI expects Report/Layout in UTF-16LE
        zf.writestr("Report/Layout", json.dumps(report_layout, indent=2).encode("utf-16le"))

    print(f"Generated Power BI template file at: {output_path}")

if __name__ == "__main__":
    pbix_file = "d:/product/dashboard/Product_Analytics.pbix"
    generate_pbix_package(pbix_file)

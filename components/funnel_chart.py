"""Funnel Chart component using ECharts."""

from nicegui import ui


def funnel_chart(data: dict) -> None:
    """
    ECharts funnel visualization for conversion stages.
    
    Args:
        data: Dict with keys: started, service_selected, staff_selected, time_selected, done
    """
    stages = [
        {"name": "Начали диалог", "value": data.get("started", 0)},
        {"name": "Выбрали услугу", "value": data.get("service_selected", 0)},
        {"name": "Выбрали мастера", "value": data.get("staff_selected", 0)},
        {"name": "Выбрали время", "value": data.get("time_selected", 0)},
        {"name": "Записались", "value": data.get("done", 0)},
    ]
    
    # Calculate percentages for labels
    total = data.get("started", 1) or 1
    
    # Lavender Theme Colors (Light to Dark Purple)
    colors = ["#F3E8FF", "#E9D5FF", "#D8B4FE", "#C084FC", "#A855F7"]
    
    ui.echart({
        "tooltip": {
            "trigger": "item",
            "formatter": "{b}: {c} ({d}%)"
        },
        "series": [{
            "type": "funnel",
            "left": "10%",
            "top": 20,
            "bottom": 20,
            "width": "80%",
            "min": 0,
            "max": total,
            "minSize": "0%",
            "maxSize": "100%",
            "sort": "descending",
            "gap": 2,
            "label": {
                "show": True,
                "position": "inside",
                "formatter": "{b}\n{c}",
                "color": "#1f2937" 
            },
            "itemStyle": {
                "borderColor": "#ffffff",
                "borderWidth": 2
            },
            "emphasis": {
                "label": {
                    "fontSize": 14,
                    "fontWeight": "bold"
                },
                "itemStyle": {
                    "shadowBlur": 10,
                    "shadowOffsetX": 0,
                    "shadowColor": "rgba(0, 0, 0, 0.5)"
                }
            },
            "data": stages,
            "color": colors
        }]
    }).classes("w-full h-80")

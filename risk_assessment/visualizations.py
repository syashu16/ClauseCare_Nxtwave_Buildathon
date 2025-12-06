"""
Risk Visualization Module

Creates visual outputs for risk assessment:
- Risk heatmaps
- Distribution charts
- Priority matrices
- Score gauges
"""

from typing import Optional
import json

from .models import (
    RiskCategory,
    SeverityLevel,
    ClauseRisk,
    DocumentRisk,
    QuickScanResult,
)


# Color schemes for risk levels
RISK_COLORS = {
    "LOW": "#28a745",       # Green
    "MEDIUM": "#ffc107",    # Yellow
    "HIGH": "#fd7e14",      # Orange
    "CRITICAL": "#dc3545",  # Red
}

CATEGORY_COLORS = {
    "financial": "#1f77b4",
    "legal_liability": "#d62728",
    "termination": "#ff7f0e",
    "intellectual_property": "#9467bd",
    "confidentiality": "#8c564b",
    "dispute_resolution": "#e377c2",
    "compliance": "#7f7f7f",
    "operational": "#17becf",
    "unknown": "#bcbd22",
}


class RiskVisualizer:
    """
    Creates visualizations for risk assessment results.
    
    Supports:
    - Plotly interactive charts
    - Matplotlib static charts
    - HTML/CSS heatmaps
    - JSON data for custom rendering
    """
    
    def __init__(self, use_plotly: bool = True):
        """
        Initialize visualizer.
        
        Args:
            use_plotly: Use Plotly for interactive charts (default True)
        """
        self.use_plotly = use_plotly
        self._plotly = None
        self._go = None
        
        if use_plotly:
            try:
                import plotly.graph_objects as go
                import plotly.express as px
                self._go = go
                self._px = px
            except ImportError:
                self.use_plotly = False
    
    def create_risk_gauge(
        self,
        score: int,
        title: str = "Overall Risk Score",
        size: int = 300,
    ):
        """
        Create a gauge chart showing risk score.
        
        Args:
            score: Risk score (0-100)
            title: Chart title
            size: Chart size in pixels
            
        Returns:
            Plotly figure or dict for custom rendering
        """
        if not self.use_plotly:
            return self._gauge_data(score, title)
        
        # Determine color based on score
        if score <= 30:
            bar_color = RISK_COLORS["LOW"]
        elif score <= 60:
            bar_color = RISK_COLORS["MEDIUM"]
        elif score <= 85:
            bar_color = RISK_COLORS["HIGH"]
        else:
            bar_color = RISK_COLORS["CRITICAL"]
        
        fig = self._go.Figure(self._go.Indicator(
            mode="gauge+number+delta",
            value=score,
            title={"text": title, "font": {"size": 16}},
            delta={"reference": 50, "increasing": {"color": "red"}, "decreasing": {"color": "green"}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "darkgray"},
                "bar": {"color": bar_color},
                "bgcolor": "white",
                "borderwidth": 2,
                "bordercolor": "gray",
                "steps": [
                    {"range": [0, 30], "color": "#e8f5e9"},
                    {"range": [30, 60], "color": "#fff8e1"},
                    {"range": [60, 85], "color": "#fff3e0"},
                    {"range": [85, 100], "color": "#ffebee"},
                ],
                "threshold": {
                    "line": {"color": "black", "width": 2},
                    "thickness": 0.75,
                    "value": score,
                },
            }
        ))
        
        fig.update_layout(
            width=size,
            height=size,
            margin=dict(l=20, r=20, t=40, b=20),
        )
        
        return fig
    
    def _gauge_data(self, score: int, title: str) -> dict:
        """Return gauge data for custom rendering"""
        if score <= 30:
            severity = "LOW"
        elif score <= 60:
            severity = "MEDIUM"
        elif score <= 85:
            severity = "HIGH"
        else:
            severity = "CRITICAL"
        
        return {
            "type": "gauge",
            "score": score,
            "title": title,
            "severity": severity,
            "color": RISK_COLORS[severity],
            "ranges": [
                {"min": 0, "max": 30, "label": "LOW", "color": RISK_COLORS["LOW"]},
                {"min": 30, "max": 60, "label": "MEDIUM", "color": RISK_COLORS["MEDIUM"]},
                {"min": 60, "max": 85, "label": "HIGH", "color": RISK_COLORS["HIGH"]},
                {"min": 85, "max": 100, "label": "CRITICAL", "color": RISK_COLORS["CRITICAL"]},
            ],
        }
    
    def create_distribution_pie(
        self,
        document_risk: DocumentRisk,
        title: str = "Risk Distribution",
    ):
        """
        Create a pie chart showing distribution of risk levels.
        
        Args:
            document_risk: Document risk assessment
            title: Chart title
            
        Returns:
            Plotly figure or dict for custom rendering
        """
        dist = document_risk.risk_summary.distribution
        
        labels = ["Critical", "High", "Medium", "Low"]
        values = [dist.critical, dist.high, dist.medium, dist.low]
        colors = [RISK_COLORS["CRITICAL"], RISK_COLORS["HIGH"], 
                  RISK_COLORS["MEDIUM"], RISK_COLORS["LOW"]]
        
        # Filter out zero values
        non_zero = [(l, v, c) for l, v, c in zip(labels, values, colors) if v > 0]
        if not non_zero:
            non_zero = [("No Risks", 1, "#cccccc")]
        
        labels, values, colors = zip(*non_zero)
        
        if not self.use_plotly:
            return {
                "type": "pie",
                "title": title,
                "data": [{"label": l, "value": v, "color": c} 
                        for l, v, c in zip(labels, values, colors)],
            }
        
        fig = self._go.Figure(data=[self._go.Pie(
            labels=labels,
            values=values,
            marker=dict(colors=colors),
            hole=0.4,
            textinfo="label+percent",
            textposition="outside",
        )])
        
        fig.update_layout(
            title=title,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2),
            margin=dict(l=20, r=20, t=60, b=60),
        )
        
        return fig
    
    def create_category_bar_chart(
        self,
        document_risk: DocumentRisk,
        title: str = "Risk by Category",
    ):
        """
        Create a bar chart showing average risk score by category.
        
        Args:
            document_risk: Document risk assessment
            title: Chart title
            
        Returns:
            Plotly figure or dict for custom rendering
        """
        categories = []
        avg_scores = []
        highest_scores = []
        colors = []
        
        for category, summary in sorted(
            document_risk.category_summaries.items(),
            key=lambda x: x[1].average_score,
            reverse=True
        ):
            cat_name = category.value.replace("_", " ").title()
            categories.append(cat_name)
            avg_scores.append(round(summary.average_score, 1))
            highest_scores.append(summary.highest_score)
            colors.append(CATEGORY_COLORS.get(category.value, "#888888"))
        
        if not self.use_plotly:
            return {
                "type": "bar",
                "title": title,
                "data": [
                    {
                        "category": cat,
                        "average_score": avg,
                        "highest_score": high,
                        "color": col,
                    }
                    for cat, avg, high, col in zip(categories, avg_scores, highest_scores, colors)
                ],
            }
        
        fig = self._go.Figure()
        
        # Add average score bars
        fig.add_trace(self._go.Bar(
            name="Average Score",
            x=categories,
            y=avg_scores,
            marker_color=colors,
            text=avg_scores,
            textposition="outside",
        ))
        
        # Add highest score markers
        fig.add_trace(self._go.Scatter(
            name="Highest Score",
            x=categories,
            y=highest_scores,
            mode="markers",
            marker=dict(size=12, symbol="diamond", color="red"),
        ))
        
        fig.update_layout(
            title=title,
            xaxis_title="Category",
            yaxis_title="Risk Score",
            yaxis=dict(range=[0, 105]),
            barmode="group",
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.3),
            margin=dict(l=40, r=20, t=60, b=100),
        )
        
        return fig
    
    def create_priority_matrix(
        self,
        clause_risks: list[ClauseRisk],
        title: str = "Risk Priority Matrix",
    ):
        """
        Create a priority matrix (impact vs likelihood).
        
        Args:
            clause_risks: List of clause risks
            title: Chart title
            
        Returns:
            Plotly figure or dict for custom rendering
        """
        # Map likelihood to numeric value
        likelihood_map = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}
        
        data = []
        for risk in clause_risks:
            likelihood = likelihood_map.get(risk.likelihood.upper(), 2)
            impact = risk.score  # Use score as impact proxy
            
            data.append({
                "clause_id": risk.clause_id,
                "likelihood": likelihood,
                "impact": impact,
                "category": risk.category.value,
                "primary_risk": risk.primary_risk[:50],
                "severity": risk.severity.value,
            })
        
        if not self.use_plotly:
            return {
                "type": "scatter_matrix",
                "title": title,
                "data": data,
                "axes": {
                    "x": {"label": "Likelihood", "range": [0.5, 3.5]},
                    "y": {"label": "Impact (Score)", "range": [0, 105]},
                },
            }
        
        # Create scatter plot
        fig = self._go.Figure()
        
        for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            severity_data = [d for d in data if d["severity"] == severity]
            if severity_data:
                fig.add_trace(self._go.Scatter(
                    x=[d["likelihood"] for d in severity_data],
                    y=[d["impact"] for d in severity_data],
                    mode="markers",
                    name=severity,
                    marker=dict(
                        size=15,
                        color=RISK_COLORS[severity],
                        line=dict(width=1, color="white"),
                    ),
                    text=[f"{d['clause_id']}: {d['primary_risk']}" for d in severity_data],
                    hoverinfo="text",
                ))
        
        # Add quadrant lines
        fig.add_hline(y=60, line_dash="dash", line_color="gray", opacity=0.5)
        fig.add_vline(x=2, line_dash="dash", line_color="gray", opacity=0.5)
        
        # Add quadrant labels
        fig.add_annotation(x=1, y=90, text="Monitor", showarrow=False, font=dict(size=10, color="gray"))
        fig.add_annotation(x=3, y=90, text="Act Now", showarrow=False, font=dict(size=10, color="red"))
        fig.add_annotation(x=1, y=20, text="Accept", showarrow=False, font=dict(size=10, color="green"))
        fig.add_annotation(x=3, y=20, text="Mitigate", showarrow=False, font=dict(size=10, color="orange"))
        
        fig.update_layout(
            title=title,
            xaxis=dict(
                title="Likelihood",
                tickvals=[1, 2, 3],
                ticktext=["Low", "Medium", "High"],
                range=[0.5, 3.5],
            ),
            yaxis=dict(
                title="Impact (Risk Score)",
                range=[0, 105],
            ),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2),
            margin=dict(l=60, r=20, t=60, b=60),
        )
        
        return fig
    
    def create_heatmap(
        self,
        text: str,
        scan_result: QuickScanResult,
        title: str = "Document Risk Heatmap",
    ) -> dict:
        """
        Create heatmap data for document visualization.
        
        Args:
            text: Original document text
            scan_result: Quick scan result
            title: Heatmap title
            
        Returns:
            Dict with heatmap data for rendering
        """
        segments = []
        last_end = 0
        
        # Sort matches by position
        all_matches = []
        for km in scan_result.keyword_matches:
            all_matches.append({
                "start": km.position[0],
                "end": km.position[1],
                "weight": km.weight,
                "keyword": km.keyword,
                "category": km.category.value,
            })
        
        for rf in scan_result.red_flags:
            # Check if not already in matches
            if not any(m["start"] == rf.position[0] for m in all_matches):
                all_matches.append({
                    "start": rf.position[0],
                    "end": rf.position[1],
                    "weight": rf.weight,
                    "keyword": rf.phrase,
                    "category": rf.category.value,
                })
        
        all_matches.sort(key=lambda x: x["start"])
        
        # Build segments
        for match in all_matches:
            # Add plain text before this match
            if match["start"] > last_end:
                segments.append({
                    "text": text[last_end:match["start"]],
                    "type": "plain",
                    "severity": None,
                })
            
            # Add highlighted match
            severity = self._weight_to_severity(match["weight"])
            segments.append({
                "text": text[match["start"]:match["end"]],
                "type": "highlight",
                "severity": severity,
                "color": RISK_COLORS[severity],
                "keyword": match["keyword"],
                "category": match["category"],
            })
            
            last_end = match["end"]
        
        # Add remaining text
        if last_end < len(text):
            segments.append({
                "text": text[last_end:],
                "type": "plain",
                "severity": None,
            })
        
        return {
            "type": "heatmap",
            "title": title,
            "segments": segments,
            "summary": {
                "total_highlights": len(all_matches),
                "categories": list(set(m["category"] for m in all_matches)),
            },
        }
    
    def _weight_to_severity(self, weight: float) -> str:
        """Convert keyword weight to severity string"""
        if weight >= 2.5:
            return "CRITICAL"
        elif weight >= 2.0:
            return "HIGH"
        elif weight >= 1.5:
            return "MEDIUM"
        else:
            return "LOW"
    
    def create_trend_chart(
        self,
        clause_risks: list[ClauseRisk],
        title: str = "Risk Trend Across Document",
    ):
        """
        Create a line chart showing risk scores across clauses.
        
        Args:
            clause_risks: List of clause risks in document order
            title: Chart title
            
        Returns:
            Plotly figure or dict for custom rendering
        """
        clause_ids = [r.clause_id for r in clause_risks]
        scores = [r.score for r in clause_risks]
        severities = [r.severity.value for r in clause_risks]
        colors = [RISK_COLORS[s] for s in severities]
        
        if not self.use_plotly:
            return {
                "type": "line",
                "title": title,
                "data": [
                    {
                        "clause_id": cid,
                        "score": score,
                        "severity": sev,
                        "color": col,
                    }
                    for cid, score, sev, col in zip(clause_ids, scores, severities, colors)
                ],
            }
        
        fig = self._go.Figure()
        
        # Add line
        fig.add_trace(self._go.Scatter(
            x=list(range(len(clause_ids))),
            y=scores,
            mode="lines+markers",
            name="Risk Score",
            line=dict(color="#333333", width=2),
            marker=dict(size=10, color=colors, line=dict(width=1, color="white")),
            text=[f"{cid}: {score}" for cid, score in zip(clause_ids, scores)],
            hoverinfo="text",
        ))
        
        # Add threshold lines
        fig.add_hline(y=85, line_dash="dash", line_color=RISK_COLORS["CRITICAL"], 
                      annotation_text="Critical", annotation_position="right")
        fig.add_hline(y=60, line_dash="dash", line_color=RISK_COLORS["HIGH"],
                      annotation_text="High", annotation_position="right")
        fig.add_hline(y=30, line_dash="dash", line_color=RISK_COLORS["MEDIUM"],
                      annotation_text="Medium", annotation_position="right")
        
        fig.update_layout(
            title=title,
            xaxis=dict(
                title="Clause Order",
                tickvals=list(range(len(clause_ids))),
                ticktext=clause_ids,
                tickangle=45,
            ),
            yaxis=dict(
                title="Risk Score",
                range=[0, 105],
            ),
            showlegend=False,
            margin=dict(l=60, r=60, t=60, b=100),
        )
        
        return fig
    
    def create_dashboard(self, document_risk: DocumentRisk) -> dict:
        """
        Create a complete dashboard with all visualizations.
        
        Args:
            document_risk: Complete document risk assessment
            
        Returns:
            Dict with all visualization data
        """
        summary = document_risk.risk_summary
        
        dashboard = {
            "overall_gauge": self.create_risk_gauge(
                summary.overall_score,
                "Overall Risk Score"
            ),
            "distribution_pie": self.create_distribution_pie(
                document_risk,
                "Risk Distribution"
            ),
            "category_bars": self.create_category_bar_chart(
                document_risk,
                "Risk by Category"
            ),
            "priority_matrix": self.create_priority_matrix(
                document_risk.clause_risks,
                "Priority Matrix"
            ),
            "trend_chart": self.create_trend_chart(
                document_risk.clause_risks,
                "Risk Trend"
            ),
            "metrics": {
                "overall_score": summary.overall_score,
                "overall_level": summary.overall_level.value,
                "total_clauses": len(document_risk.clause_risks),
                "critical_count": summary.distribution.critical,
                "high_count": summary.distribution.high,
                "medium_count": summary.distribution.medium,
                "low_count": summary.distribution.low,
                "favorability": document_risk.overall_favorability,
            },
            "top_risks_table": [
                {
                    "rank": r.rank,
                    "clause": r.clause_reference,
                    "score": r.score,
                    "issue": r.issue,
                }
                for r in document_risk.top_risks[:5]
            ],
        }
        
        return dashboard
    
    def render_html_heatmap(self, heatmap_data: dict) -> str:
        """
        Render heatmap data as HTML.
        
        Args:
            heatmap_data: Heatmap data from create_heatmap()
            
        Returns:
            HTML string
        """
        html_parts = [
            '<div class="risk-heatmap" style="font-family: Arial, sans-serif; line-height: 1.6;">',
            f'<h3>{heatmap_data["title"]}</h3>',
            '<div class="document-text">',
        ]
        
        for segment in heatmap_data["segments"]:
            if segment["type"] == "plain":
                text = segment["text"].replace("\n", "<br>")
                html_parts.append(f'<span>{text}</span>')
            else:
                color = segment["color"]
                text = segment["text"]
                tooltip = f'{segment["category"]}: {segment["keyword"]}'
                html_parts.append(
                    f'<span style="background-color: {color}; padding: 2px 4px; '
                    f'border-radius: 3px; cursor: help;" title="{tooltip}">{text}</span>'
                )
        
        html_parts.extend([
            '</div>',
            '<div class="legend" style="margin-top: 20px;">',
            '<strong>Legend:</strong> ',
        ])
        
        for level, color in RISK_COLORS.items():
            html_parts.append(
                f'<span style="background-color: {color}; padding: 2px 8px; '
                f'margin: 0 5px; border-radius: 3px;">{level}</span>'
            )
        
        html_parts.extend(['</div>', '</div>'])
        
        return "".join(html_parts)
    
    def to_json(self, figure) -> str:
        """Convert a Plotly figure to JSON for API response"""
        if self.use_plotly and hasattr(figure, 'to_json'):
            return figure.to_json()
        return json.dumps(figure)

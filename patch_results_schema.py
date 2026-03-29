--- src/blockbt/api/routes/results.py
+++ src/blockbt/api/routes/results.py
@@ -10,6 +10,11 @@

 router = APIRouter(dependencies=[Depends(get_api_key)])

+from pydantic import BaseModel
+class AIAnalysisResponse(BaseModel):
+    prompt: str | None
+    report: str
+
 @router.get("/{sim_id}")
 def get_simulation_result(sim_id: int) -> dict[str, Any]:
     """Retrieve the status and metrics of a backtest run by its Simulation ID."""
@@ -35,8 +40,8 @@
             "error_log": sim.error_log,
         }

-@router.post("/{sim_id}/analyze")
-def analyze_simulation_result(sim_id: int) -> dict[str, Any]:
+@router.post("/{sim_id}/analyze", response_model=AIAnalysisResponse)
+def analyze_simulation_result(sim_id: int) -> AIAnalysisResponse:
     """Generate an AI analysis report for a completed simulation."""
     with get_session() as db:
         sim = db.get(SimulationResult, sim_id)
@@ -49,7 +54,7 @@
             )

         if sim.ai_analysis_report:
-            return {"prompt": None, "report": sim.ai_analysis_report}
+            return AIAnalysisResponse(prompt=None, report=sim.ai_analysis_report)

         result = sim.full_metrics_json or {}
         result["symbol"] = sim.symbol
@@ -82,4 +87,4 @@
         sim.ai_analysis_report = OllamaClient().generate_report(prompt)
         db.commit()

-        return {"prompt": prompt, "report": sim.ai_analysis_report}
+        return AIAnalysisResponse(prompt=prompt, report=sim.ai_analysis_report)

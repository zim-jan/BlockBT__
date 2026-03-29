--- src/blockbt/api/routes/results.py
+++ src/blockbt/api/routes/results.py
@@ -45,7 +45,9 @@
             raise HTTPException(status_code=404, detail="Simulation Result not found")

         if sim.status.upper() != "COMPLETED":
-            raise HTTPException(status_code=400, detail="Cannot analyze a simulation that is not completed.")
+            raise HTTPException(
+                status_code=400, detail="Cannot analyze a simulation that is not completed."
+            )

         if sim.ai_analysis_report:
             return {"prompt": None, "report": sim.ai_analysis_report}
@@ -71,7 +73,11 @@
         strategy_name = sim.strategy_template.name if sim.strategy_template else "Unknown Strategy"
         raw_params = sim.strategy_template.wizard_state if sim.strategy_template else {}

-        payload = ReportBuilder.build(result=result, strategy_name=strategy_name, raw_params=raw_params)
+        payload = ReportBuilder.build(
+            result=result,
+            strategy_name=strategy_name,
+            raw_params=raw_params
+        )
         prompt = payload.to_prompt()
         sim.ai_analysis_report = OllamaClient().generate_report(prompt)
         db.commit()

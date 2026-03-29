--- src/blockbt/api/routes/results.py
+++ src/blockbt/api/routes/results.py
@@ -88,3 +88,4 @@
         prompt = payload.to_prompt()
         sim.ai_analysis_report = OllamaClient().generate_report(prompt)
         db.commit()
+        return AIAnalysisResponse(prompt=prompt, report=sim.ai_analysis_report)

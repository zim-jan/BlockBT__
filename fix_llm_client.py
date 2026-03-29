
filename = "src/blockbt/mcp/llm_client.py"
with open(filename) as f:
    content = f.read()

content = content.replace(
    '"Jesteś głównym analitykiem finansowym (Quant). Twoim zadaniem jest ocena wyników strategii algorytmicznej. "',
    '"Jesteś głównym analitykiem finansowym (Quant). "\n    "Twoim zadaniem jest ocena wyników strategii algorytmicznej. "'
)

content = content.replace(
    '"Zignoruj techniczną strukturę pliku JSON i skup się wyłącznie na liczbach. Zinterpretuj wskaźnik Sharpe\'a, "',
    '"Zignoruj techniczną strukturę pliku JSON i skup się wyłącznie na liczbach. "\n    "Zinterpretuj wskaźnik Sharpe\'a, "'
)

content = content.replace(
    '"Max Drawdown oraz Win Rate. Napisz zwięzły, profesjonalny wniosek na temat ryzyka i stabilności tej strategii. "',
    '"Max Drawdown oraz Win Rate. Napisz zwięzły, profesjonalny wniosek "\n    "na temat ryzyka i stabilności tej strategii. "'
)

with open(filename, "w") as f:
    f.write(content)


def get_filters(last_user_msg):
    rag_filters = {}
    
    # Simple keyword heuristic for demo (can be upgraded to LLM classification)
    if any(w in last_user_msg.lower() for w in ["precio", "cuánto", "costo", "garantía", "factura", "contrato"]):
        rag_filters["doc_category"] = "financial_legal"
    elif any(w in last_user_msg.lower() for w in ["fecha", "horario", "temario", "cuando", "cuándo", "donde", "dónde", "entregable"]):
        rag_filters["doc_category"] = "product_logic"
    elif any(w in last_user_msg.lower() for w in ["miedo", "no sé", "pensar", "esposo", "duda", "segura"]):
        # Map to persuasion and avatar psychology
        rag_filters["doc_category"] = ["sales_persuasion", "avatar_psychology"]
        
    return rag_filters

def test_logic():
    test_cases = [
        ("¿Cuál es el precio?", "financial_legal"),
        ("Dame la factura", "financial_legal"),
        ("¿Cuándo empieza?", "product_logic"),
        ("¿Dónde es el evento?", "product_logic"),
        ("Tengo miedo de invertir", ["sales_persuasion", "avatar_psychology"]),
        ("No sé si es para mí", ["sales_persuasion", "avatar_psychology"]),
        ("Hola, ¿cómo estás?", None)
    ]
    
    for msg, expected in test_cases:
        result = get_filters(msg).get("doc_category")
        if result == expected:
            print(f"PASS: '{msg}' -> {result}")
        else:
            print(f"FAIL: '{msg}' -> Expected {expected}, got {result}")

if __name__ == "__main__":
    test_logic()

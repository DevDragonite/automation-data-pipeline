"""
╔══════════════════════════════════════════════════════════════╗
║     MARKET BASKET ANALYSIS — AUTOMATED PIPELINE RUNNER      ║
║     Activado automáticamente por n8n cada lunes 8am         ║
║     Autor: Hely Camargo                                      ║
╚══════════════════════════════════════════════════════════════╝
"""

import pandas as pd
import numpy as np
from mlxtend.frequent_patterns import apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder
import os
import json
import datetime
import traceback

# ── CONFIGURACIÓN ──
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
LOG_FILE = os.path.join(OUTPUT_DIR, "pipeline_log.txt")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def log(msg):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] {msg}"
    print(entry)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry + "\n")

def load_fresh_data():
    """
    Carga los datos frescos generados por n8n.
    Si no existen, usa el dataset original como fallback.
    """
    fresh_path = os.path.join(DATA_DIR, "fresh_transactions.csv")
    original_path = os.path.join(DATA_DIR, "Reviews.csv")

    if os.path.exists(fresh_path):
        log("✅ Datos frescos de n8n encontrados — cargando fresh_transactions.csv")
        df = pd.read_csv(fresh_path)
        log(f"   → {len(df)} transacciones cargadas")
        return df, "fresh"
    elif os.path.exists(original_path):
        log("⚠️  Datos frescos no encontrados — usando dataset original como fallback")
        df = pd.read_csv(original_path)
        log(f"   → {len(df)} registros del dataset original")
        return df, "original"
    else:
        raise FileNotFoundError(
            "No se encontró ningún dataset. "
            "Asegúrate de que n8n ejecutó el pipeline o que el dataset original está en data/"
        )

def prepare_basket_matrix(df, source):
    """
    Prepara la matriz binaria de transacciones para Apriori.
    Adapta el procesamiento según la fuente de datos.
    """
    log("🔄 Preparando basket matrix...")

    if source == "fresh":
        # Datos de Open Food Facts via n8n
        # Cada fila es un par product_a, product_b por categoría
        transactions = []
        for category in df['category'].unique():
            cat_products = df[df['category'] == category]['product_a'].tolist()
            cat_products += df[df['category'] == category]['product_b'].tolist()
            cat_products = list(set(cat_products))
            if len(cat_products) >= 2:
                # Simular transacciones: cada par de productos es una compra
                for i in range(0, len(cat_products) - 1, 2):
                    transactions.append([cat_products[i], cat_products[i+1]])
                    if i + 2 < len(cat_products):
                        transactions.append([cat_products[i], cat_products[i+2]])
    else:
        # Dataset original: agrupar por InvoiceNo si existe
        if 'InvoiceNo' in df.columns and 'Description' in df.columns:
            df_uk = df[df.get('Country', pd.Series(['UK']*len(df))) == 'United Kingdom'].copy()
            df_uk = df_uk[df_uk['Quantity'] > 0]
            df_uk['Description'] = df_uk['Description'].str.strip().str.upper()
            transactions = df_uk.groupby('InvoiceNo')['Description'].apply(list).tolist()
        else:
            log("⚠️  Formato desconocido — generando transacciones sintéticas para demo")
            np.random.seed(42)
            products = ['CANDLE', 'HOLDER', 'GIFT BAG', 'RIBBON', 'BOX',
                       'TISSUE', 'FRAME', 'VASE', 'LAMP', 'CUSHION']
            transactions = [
                list(np.random.choice(products, size=np.random.randint(2, 5), replace=False))
                for _ in range(500)
            ]

    log(f"   → {len(transactions)} transacciones preparadas")
    return transactions

def run_apriori(transactions):
    """
    Ejecuta el algoritmo Apriori y genera reglas de asociación.
    """
    log("🧮 Ejecutando algoritmo Apriori...")

    te = TransactionEncoder()
    te_array = te.fit(transactions).transform(transactions)
    basket_matrix = pd.DataFrame(te_array, columns=te.columns_)

    # Apriori con soporte mínimo de 1%
    frequent_itemsets = apriori(
        basket_matrix,
        min_support=0.01,
        use_colnames=True,
        max_len=2
    )

    if len(frequent_itemsets) == 0:
        log("⚠️  No se encontraron itemsets frecuentes con soporte 1% — bajando a 0.5%")
        frequent_itemsets = apriori(
            basket_matrix,
            min_support=0.005,
            use_colnames=True,
            max_len=2
        )

    log(f"   → {len(frequent_itemsets)} itemsets frecuentes encontrados")

    # Reglas de asociación con lift > 1.0
    rules = association_rules(
        frequent_itemsets,
        metric="lift",
        min_threshold=1.0
    )

    # Filtrar reglas de pares (no singles)
    rules = rules[rules['antecedents'].apply(len) == 1]
    rules = rules[rules['consequents'].apply(len) == 1]

    # Formatear para exportar
    rules['antecedents'] = rules['antecedents'].apply(lambda x: ', '.join(list(x)))
    rules['consequents'] = rules['consequents'].apply(lambda x: ', '.join(list(x)))
    rules['run_date'] = datetime.datetime.now().strftime("%Y-%m-%d")

    rules = rules.sort_values('lift', ascending=False)

    log(f"   → {len(rules)} reglas de asociación generadas")
    return rules, frequent_itemsets

def generate_executive_summary(rules, frequent_itemsets):
    """
    Genera resumen ejecutivo con los hallazgos más importantes.
    """
    top_rules = rules.head(10)

    summary = {
        "run_date": datetime.datetime.now().strftime("%Y-%m-%d"),
        "timestamp": datetime.datetime.now().isoformat(),
        "total_rules": len(rules),
        "total_itemsets": len(frequent_itemsets),
        "top_lift": round(float(rules['lift'].max()), 2) if len(rules) > 0 else 0,
        "avg_lift_top10": round(float(top_rules['lift'].mean()), 2) if len(top_rules) > 0 else 0,
        "max_confidence": round(float(rules['confidence'].max()), 2) if len(rules) > 0 else 0,
        "top_association": f"{top_rules.iloc[0]['antecedents']} → {top_rules.iloc[0]['consequents']}" if len(top_rules) > 0 else "N/A",
        "top_lift_value": round(float(top_rules.iloc[0]['lift']), 2) if len(top_rules) > 0 else 0,
        "business_impact": {
            "high_lift_rules": len(rules[rules['lift'] > 5]),
            "medium_lift_rules": len(rules[(rules['lift'] >= 3) & (rules['lift'] <= 5)]),
            "high_confidence_rules": len(rules[rules['confidence'] > 0.5])
        }
    }
    return summary

def save_outputs(rules, frequent_itemsets, summary):
    """
    Guarda todos los outputs del pipeline.
    """
    log("💾 Guardando outputs...")

    # Reglas de asociación
    rules_path = os.path.join(OUTPUT_DIR, "fresh_rules_asociacion.csv")
    rules.to_csv(rules_path, index=False)
    log(f"   ✅ {rules_path}")

    # Itemsets frecuentes
    itemsets_df = frequent_itemsets.copy()
    itemsets_df['itemsets'] = itemsets_df['itemsets'].apply(lambda x: ', '.join(list(x)))
    itemsets_path = os.path.join(OUTPUT_DIR, "fresh_frequent_itemsets.csv")
    itemsets_df.to_csv(itemsets_path, index=False)
    log(f"   ✅ {itemsets_path}")

    # Resumen ejecutivo JSON
    summary_path = os.path.join(OUTPUT_DIR, "pipeline_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    log(f"   ✅ {summary_path}")

    # Top 10 reglas en CSV separado para el dashboard
    top_rules_path = os.path.join(OUTPUT_DIR, "top10_rules.csv")
    rules.head(10).to_csv(top_rules_path, index=False)
    log(f"   ✅ {top_rules_path}")

    return summary_path

def print_final_report(summary):
    """
    Imprime el reporte final en consola — n8n captura este output.
    """
    report = f"""
╔══════════════════════════════════════════════════════╗
║           PIPELINE EJECUTADO EXITOSAMENTE            ║
╠══════════════════════════════════════════════════════╣
║  Fecha:              {summary['run_date']}                    
║  Reglas generadas:   {summary['total_rules']}                        
║  Lift máximo:        {summary['top_lift']}x                      
║  Lift promedio top10:{summary['avg_lift_top10']}x                    
║  Confianza máxima:   {summary['max_confidence']*100:.0f}%                    
╠══════════════════════════════════════════════════════╣
║  TOP ASOCIACIÓN:                                     
║  {summary['top_association'][:48]}
║  Lift: {summary['top_lift_value']}x                            
╠══════════════════════════════════════════════════════╣
║  IMPACTO DE NEGOCIO:                                 
║  Reglas Lift>5:   {summary['business_impact']['high_lift_rules']} (recomendación on-site)  
║  Reglas Lift 3-5: {summary['business_impact']['medium_lift_rules']} (bundle con descuento)  
║  Alta Confianza:  {summary['business_impact']['high_confidence_rules']} (trigger en checkout)   
╚══════════════════════════════════════════════════════╝
PIPELINE_SUCCESS
"""
    print(report)
    log(report)

def main():
    log("=" * 60)
    log("🚀 INICIANDO MARKET BASKET PIPELINE RUNNER")
    log("=" * 60)

    try:
        # Paso 1: Cargar datos
        df, source = load_fresh_data()

        # Paso 2: Preparar transacciones
        transactions = prepare_basket_matrix(df, source)

        # Paso 3: Ejecutar Apriori
        rules, frequent_itemsets = run_apriori(transactions)

        # Paso 4: Generar resumen
        summary = generate_executive_summary(rules, frequent_itemsets)

        # Paso 5: Guardar outputs
        save_outputs(rules, frequent_itemsets, summary)

        # Paso 6: Reporte final
        print_final_report(summary)

        return 0

    except Exception as e:
        error_msg = f"❌ ERROR CRÍTICO: {str(e)}\n{traceback.format_exc()}"
        log(error_msg)
        print("PIPELINE_ERROR")
        print(error_msg)
        return 1

if __name__ == "__main__":
    exit(main())

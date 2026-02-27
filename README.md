# 🔄 Auto 1 — Market Basket Data Pipeline Viviente

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![n8n](https://img.shields.io/badge/n8n-Self--Hosted-FF6D5A.svg)](https://n8n.io/)
[![Automation](https://img.shields.io/badge/Automation-Weekly-green.svg)]()
[![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)]()

**Automatización que transforma el Market Basket Analysis de un proyecto estático a un sistema vivo.** Cada lunes a las 8am, n8n descarga productos frescos de la API de Open Food Facts, los procesa, ejecuta el algoritmo Apriori automáticamente y envía un reporte ejecutivo — sin intervención humana.

---

## 🏗️ Arquitectura del Pipeline

```
⏰ Schedule Trigger (Lunes 8am)
        │
        ▼
🌐 HTTP Request ──────────────────────────────────────────
│  API: Open Food Facts (world.openfoodfacts.org)         │
│  Endpoint: /cgi/search.pl                               │
│  Parámetros: 200 productos de snacks, JSON format       │
└─────────────────────────────────────────────────────────┘
        │
        ▼
🔧 Code Node — Limpieza y Transformación
│  • Filtra productos sin nombre
│  • Normaliza texto (lowercase, sin caracteres especiales)
│  • Agrupa por categoría
│  • Genera pares de transacciones por categoría
└─────────────────────────────────────────────
        │
        ▼
📄 Code Node — Generar CSVs
│  • Produce fresh_products.csv
│  • Produce fresh_transactions.csv
│  • Genera log de ejecución
└─────────────────────────────────
        │
        ▼
⚡ Execute Command — Pipeline Python
│  • Activa pipeline_runner.py
│  • Corre algoritmo Apriori con datos frescos
│  • Genera reglas de asociación actualizadas
│  • Exporta outputs a /output/
└─────────────────────────────────
        │
        ▼
🔀 IF Node — ¿Éxito o Error?
    │                 │
    ▼                 ▼
✅ Éxito          ❌ Error
Reporte con       Alerta con
métricas          diagnóstico
    │                 │
    └────────┬─────────┘
             ▼
        📝 Log Final
```

---

## 📁 Estructura de Archivos

```
automation-01-data-pipeline/
├── market_basket_workflow.json    ← Importar en n8n (flujo completo)
├── pipeline_runner.py             ← Script Python activado por n8n
├── README.md                      ← Esta documentación
└── outputs_ejemplo/               ← Outputs de muestra
    ├── fresh_rules_asociacion.csv
    ├── fresh_frequent_itemsets.csv
    ├── top10_rules.csv
    ├── pipeline_summary.json
    └── pipeline_log.txt
```

---

## ⚙️ Instalación y Configuración

### Prerequisitos
- Node.js v18+
- Python 3.9+
- Proyecto `market-basket-analysis` ya configurado

### 1. Instalar n8n
```bash
npm install -g n8n
n8n start
# Abre http://localhost:5678
```

### 2. Instalar dependencias Python
```bash
cd market-basket-analysis
pip install mlxtend pandas numpy
```

### 3. Importar el workflow en n8n
1. Abre n8n en `http://localhost:5678`
2. Menú superior derecho → **Import from JSON**
3. Pega el contenido de `market_basket_workflow.json`
4. Click en **Import**

### 4. Configurar la ruta del proyecto
En el nodo **⚡ Execute — Correr Pipeline Python**, actualiza la ruta:
```
cd /TU/RUTA/REAL/market-basket-analysis && python pipeline_runner.py
```

### 5. Activar el workflow
Toggle **Active** en la esquina superior derecha de n8n.

---

## 📊 Outputs Generados Automáticamente

| Archivo | Contenido | Actualización |
|---------|-----------|---------------|
| `fresh_rules_asociacion.csv` | Todas las reglas con soporte, confianza y lift | Semanal |
| `fresh_frequent_itemsets.csv` | Itemsets frecuentes del período | Semanal |
| `top10_rules.csv` | Top 10 asociaciones por lift | Semanal |
| `pipeline_summary.json` | KPIs del pipeline en JSON | Semanal |
| `pipeline_log.txt` | Log completo de cada ejecución | Acumulativo |

---

## 🔍 Hallazgos Clave Demostrados

1. **Sistema vivo**: El dashboard Streamlit muestra datos de la semana actual, no de 2018
2. **Cero intervención**: El pipeline corre sin que el analista toque nada
3. **Trazabilidad completa**: Cada ejecución queda documentada con timestamp en el log
4. **Manejo de errores**: Si la API falla o Python da error, el sistema envía una alerta automática

---

## 🔧 Decisiones Técnicas

**¿Por qué Open Food Facts API?**
Gratuita, sin autenticación requerida, con 800K+ productos reales de retail global. Perfecta para demostrar integración con APIs externas sin depender de APIs de pago.

**¿Por qué n8n self-hosted?**
Independencia total de restricciones geográficas. El workflow corre en tu propia máquina sin necesitar servidores externos ni cuentas de terceros.

**¿Por qué el IF node?**
Un pipeline de producción real siempre tiene manejo de errores. El IF node demuestra que este sistema está diseñado para fallar con gracia, no para romperse silenciosamente.


#MarketBasketAnalysis #DataEngineering
```

---

*Desarrollado por Hely Camargo — Python · n8n · Pandas · mlxtend*

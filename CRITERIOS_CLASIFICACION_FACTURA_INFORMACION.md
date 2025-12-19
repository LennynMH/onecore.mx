# 📋 Criterios y Keywords para Clasificación: FACTURA vs INFORMACIÓN

## 🎯 Sistema de Clasificación

El sistema usa un **sistema de pesos con keywords** para clasificar documentos como **FACTURA** o **INFORMACIÓN**.

---

## 🔑 Keywords por Categoría

### 1. Keywords CRÍTICAS (3 puntos cada una)

**Indican directamente que es una factura:**

| Keyword | Variaciones |
|---------|-------------|
| `factura` | factura |
| `invoice` | invoice |
| `recibo` | recibo |
| `receipt` | receipt |
| `bill` | bill |
| `número de factura` | número de factura, numero de factura |
| `invoice number` | invoice number, invoice no |
| `factura no` | factura no, factura numero |

**Ejemplos en texto:**
- "FACTURA No. 12345"
- "Invoice number: INV-001"
- "Recibo de pago"

---

### 2. Keywords IMPORTANTES (2 puntos cada una)

**Indican contexto de factura (comúnmente aparecen en facturas):**

| Categoría | Keywords |
|-----------|----------|
| **Cliente** | `cliente`, `client`, `customer` |
| **Proveedor** | `proveedor`, `provider`, `vendor`, `supplier` |
| **Totales** | `total`, `subtotal`, `iva`, `tax`, `impuesto` |
| **Cantidad** | `cantidad`, `quantity`, `qty` |
| **Precio** | `precio unitario`, `unit price`, `precio`, `unitario` |
| **Producto** | `producto`, `product`, `item` |
| **Identificación Fiscal** | `rfc`, `tax id`, `cuit` |

**Ejemplos en texto:**
- "Cliente: Juan Pérez"
- "Proveedor: Empresa XYZ"
- "Total: $1,000.00"
- "IVA: $160.00"
- "Cantidad: 5"
- "Precio unitario: $200.00"
- "Producto: Servicio de Consultoría"
- "RFC: ABC123456XYZ"

---

### 3. Keywords SECUNDARIAS (1 punto cada una)

**Palabras comunes que pueden aparecer en facturas pero también en otros documentos:**

| Categoría | Keywords |
|-----------|----------|
| **Cliente/Proveedor (variaciones)** | `comprador`, `buyer`, `vendedor`, `seller` |
| **Impuestos (variaciones)** | `taxes` |
| **Cantidad (variaciones)** | `qty.`, `cant.` |
| **Producto (variaciones)** | `articulo`, `article` |
| **Servicio** | `servicio`, `service` ⚠️ Muy común en documentos informativos |
| **Fecha** | `fecha de factura`, `invoice date`, `date`, `fecha` ⚠️ Muy común |
| **Pago** | `pago`, `payment`, `metodo de pago`, `payment method` |
| **Detalle** | `detalle`, `detail`, `concepto`, `concept` |

**⚠️ Nota:** Keywords como "servicio" y "fecha" son muy comunes en documentos informativos, por eso tienen menor peso.

---

## 📊 Sistema de Puntuación

### Cálculo del Score

```
Score Total = (Keywords Críticas × 3) + (Keywords Importantes × 2) + (Keywords Secundarias × 1)
```

**Ejemplo:**
- 1 keyword crítica ("factura") = 3 puntos
- 2 keywords importantes ("cliente", "proveedor") = 4 puntos
- 2 keywords secundarias ("fecha", "servicio") = 2 puntos
- **Score Total = 9 puntos**

---

## ✅ Reglas de Clasificación

El documento se clasifica como **FACTURA** si cumple **CUALQUIERA** de estas reglas:

### Regla 1: Keyword Crítica + Keywords Importantes
```
✅ 1+ keyword crítica
✅ 2+ keywords importantes
✅ Score total >= 12
→ FACTURA
```

**Ejemplo:**
- Keywords: "factura" (crítica), "cliente", "proveedor" (importantes), "total" (importante)
- Score: 3 + 2 + 2 + 2 = 9 puntos
- ❌ No cumple (necesita score >= 12)

**Ejemplo que SÍ cumple:**
- Keywords: "factura" (crítica), "cliente", "proveedor", "total", "iva", "cantidad" (importantes)
- Score: 3 + 2 + 2 + 2 + 2 + 2 = 13 puntos
- ✅ Cumple → FACTURA

---

### Regla 2: Múltiples Keywords Críticas
```
✅ 2+ keywords críticas
✅ Score total >= 10
→ FACTURA
```

**Ejemplo:**
- Keywords: "factura", "número de factura" (críticas), "cliente" (importante)
- Score: 3 + 3 + 2 = 8 puntos
- ❌ No cumple (necesita score >= 10)

**Ejemplo que SÍ cumple:**
- Keywords: "factura", "número de factura" (críticas), "cliente", "proveedor" (importantes)
- Score: 3 + 3 + 2 + 2 = 10 puntos
- ✅ Cumple → FACTURA

---

### Regla 3: Muchas Keywords Importantes
```
✅ 4+ keywords importantes
✅ Score total >= 14
→ FACTURA
```

**Ejemplo:**
- Keywords: "cliente", "proveedor", "total", "iva", "cantidad", "precio" (importantes)
- Score: 2 + 2 + 2 + 2 + 2 + 2 = 12 puntos
- ❌ No cumple (necesita score >= 14)

**Ejemplo que SÍ cumple:**
- Keywords: "cliente", "proveedor", "total", "subtotal", "iva", "cantidad", "precio", "producto" (importantes)
- Score: 2 + 2 + 2 + 2 + 2 + 2 + 2 + 2 = 16 puntos
- ✅ Cumple → FACTURA

---

### Regla 4: Score Muy Alto
```
✅ Score total >= 16
→ FACTURA
```

**Ejemplo:**
- Keywords: "factura" (crítica), "cliente", "proveedor", "total", "iva", "cantidad", "precio", "producto", "rfc" (importantes)
- Score: 3 + 2 + 2 + 2 + 2 + 2 + 2 + 2 + 2 = 19 puntos
- ✅ Cumple → FACTURA

---

### Regla 5: Por Defecto
```
❌ No cumple ninguna regla anterior
→ INFORMACIÓN
```

---

## 📝 Ejemplos Prácticos

### Ejemplo 1: Factura Típica ✅

**Texto extraído:**
```
FACTURA No. 12345
Cliente: Juan Pérez
Proveedor: Empresa XYZ
Total: $1,000.00
IVA: $160.00
Cantidad: 5
Precio unitario: $200.00
Producto: Servicio de Consultoría
RFC: ABC123456XYZ
```

**Keywords encontradas:**
- Críticas: "factura", "número de factura" (2) = 6 puntos
- Importantes: "cliente", "proveedor", "total", "iva", "cantidad", "precio unitario", "precio", "producto", "rfc" (9) = 18 puntos
- Secundarias: "servicio" (1) = 1 punto

**Score Total: 25 puntos**

**Clasificación:** ✅ **FACTURA** (cumple Regla 4: score >= 16)

---

### Ejemplo 2: Documento Informático ✅

**Texto extraído:**
```
INFORME MENSUAL DE VENTAS
Fecha: 18/12/2025
Mejora en la satisfacción del cliente
Implementación exitosa de nuevas estrategias
Servicio al cliente mejorado
```

**Keywords encontradas:**
- Críticas: "factura" (1) = 3 puntos ⚠️ (aparece en el texto)
- Importantes: "cliente", "client" (2) = 4 puntos
- Secundarias: "fecha", "servicio" (2) = 2 puntos

**Score Total: 9 puntos**

**Clasificación:** ✅ **INFORMACIÓN** (no cumple ninguna regla)

**Nota:** Aunque tiene "factura" (crítica), no tiene 2+ keywords importantes adicionales, y el score (9) es menor a 12.

---

### Ejemplo 3: Documento Ambiguo (FACTURA) ✅

**Texto extraído:**
```
Recibo de Pago
Cliente: María González
Proveedor: Servicios ABC
Total: $500.00
IVA: $80.00
```

**Keywords encontradas:**
- Críticas: "recibo" (1) = 3 puntos
- Importantes: "cliente", "proveedor", "total", "iva" (4) = 8 puntos
- Secundarias: ninguna = 0 puntos

**Score Total: 11 puntos**

**Clasificación:** ✅ **FACTURA** (cumple Regla 1: 1+ crítica + 2+ importantes + score >= 12)

**Espera...** El score es 11, no 12. ❌ No cumple.

**Clasificación real:** ✅ **INFORMACIÓN** (no cumple ninguna regla)

---

## 🎯 Resumen de Criterios

### Para ser clasificado como FACTURA:

1. **Debe tener keywords críticas** (factura, invoice, recibo, etc.) **Y** keywords importantes (cliente, proveedor, total, etc.)
2. **O** múltiples keywords críticas
3. **O** muchas keywords importantes (4+)
4. **O** un score muy alto (>= 16)

### Para ser clasificado como INFORMACIÓN:

- **No cumple ninguna** de las reglas anteriores
- Tiene pocas keywords o keywords muy comunes (fecha, servicio, etc.)
- Score total < 12 (o no cumple las combinaciones requeridas)

---

## 📊 Tabla de Referencia Rápida

| Tipo de Keyword | Puntos | Ejemplos |
|----------------|--------|----------|
| **Crítica** | 3 | factura, invoice, recibo, número de factura |
| **Importante** | 2 | cliente, proveedor, total, iva, cantidad, precio, producto, rfc |
| **Secundaria** | 1 | fecha, servicio, pago, detalle, concepto |

---

## 🔍 Cómo Ver los Criterios en Acción

**Los logs de la API muestran:**

```
INFO: Classification analysis: 8 keywords found
INFO:   Critical (2): factura, número de factura
INFO:   Important (5): cliente, proveedor, total, iva, cantidad
INFO:   Secondary (1): fecha
INFO:   Weighted score: 19 (critical: 6, important: 10, secondary: 1)
INFO: Document classified as FACTURA (rule 4: total score >= 16)
```

---

## ✅ Conclusión

**El sistema diferencia FACTURA de INFORMACIÓN usando:**

1. ✅ **Keywords críticas** (factura, invoice, recibo) - 3 puntos
2. ✅ **Keywords importantes** (cliente, proveedor, total, iva, etc.) - 2 puntos
3. ✅ **Keywords secundarias** (fecha, servicio, pago, etc.) - 1 punto
4. ✅ **Reglas estrictas** que requieren combinaciones específicas
5. ✅ **Sistema de pesos** que evita falsos positivos

**Esto asegura que solo documentos que realmente son facturas se clasifiquen como FACTURA.** 🎯


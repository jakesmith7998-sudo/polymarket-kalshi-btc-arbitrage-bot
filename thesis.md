Aquí tienes todos los ejemplos y fórmulas en formato Markdown, listos para copiar y usar.

---

# Arbitrage entre dos plataformas

### Fórmulas y ejemplos con (C = 100€)

## Fórmulas básicas

* Precios:

  * (p_A): precio del “Sí” en plataforma A
  * (p_B): precio del “No” en plataforma B

* Condición de arbitraje:
  [
  p_A + p_B < 1
  ]

* Stakes óptimos:
  [
  x = y = \frac{C}{p_A + p_B}
  ]

* Ganancia asegurada:
  [
  \text{profit} = C \cdot \frac{1 - p_A - p_B}{p_A + p_B}
  ]

---

# Ejemplo 1

* (p_A = 0.47)
* (p_B = 0.48)

### Cálculos

[
p_A + p_B = 0.95 < 1
]

[
x = y = \frac{100}{0.95} = 105.2632
]

**Costes**

* “Sí”:
  [
  105.2632 \cdot 0.47 = 49.4737€
  ]
* “No”:
  [
  105.2632 \cdot 0.48 = 50.5263€
  ]

**Ganancia segura**
[
100 \cdot \frac{1 - 0.95}{0.95} = 5.2632€
]

---

# Ejemplo 2

* (p_A = 0.35)
* (p_B = 0.55)

### Cálculos

[
p_A + p_B = 0.90 < 1
]

[
x = y = \frac{100}{0.90} = 111.1111
]

**Costes**

* “Sí”:
  [
  111.1111 \cdot 0.35 = 38.8889€
  ]
* “No”:
  [
  111.1111 \cdot 0.55 = 61.1111€
  ]

**Ganancia segura**
[
100 \cdot \frac{1 - 0.90}{0.90} = 11.1111€
]

---

# Ejemplo 3

* (p_A = 0.62)
* (p_B = 0.30)

### Cálculos

[
p_A + p_B = 0.92 < 1
]

[
x = y = \frac{100}{0.92} = 108.6957
]

**Costes**

* “Sí”:
  [
  108.6957 \cdot 0.62 = 67.3913€
  ]
* “No”:
  [
  108.6957 \cdot 0.30 = 32.6087€
  ]

**Ganancia segura**
[
100 \cdot \frac{1 - 0.92}{0.92} = 8.6957€
]

---

Si quieres, te genero una plantilla en Markdown para pegar tus propios precios de Polymarket y Kalshi y que puedas hacer los cálculos al instante.

# P-Adic Embedding Algorithm: Exact Reference from Chistyakov (1996)

## Source
- **Paper**: "Fractal Geometry for Images of Continuous Embeddings of p-Adic Numbers and Solenoids into Euclidean Spaces"
- **Author**: D. V. Chistyakov
- **Journal**: Theoretical and Mathematical Physics, Vol. 109, No. 3, pp. 1495-1507 (December 1996)
- **File**: BF02073866.pdf

---

## 1. EXACT MATHEMATICAL FORMULATION

### Definition 3 (Page 5, Equation 15)
The fundamental embedding formula is:

```
T_s^(m)(x) = (1 - s^v(x))/(1 - s) + Σ_{n=v(x)}^{l-1} s^n χ_n^(m)(x)  ∀x ∈ Q_p
```

Where:
- `T_s^(m)`: The embedding map from Q_p → C
- `m ∈ ℕ ∪ {∞}`: Character truncation level
- `s ∈ U_1 = {z ∈ ℂ : |z| < 1}`: Complex scaling parameter
- `v(x)`: P-adic valuation (position of first nonzero digit)
- `χ_n^(m)(x)`: Additive character (see below)
- `l`: Depth of embedding (number of digits in p-adic representation)

### Additive Character (Page 5, Equation 14)

```
χ_n^(m)(x) = exp(i2π/p Σ_{k=0}^m x_{n-k}p^{-k})  ∀x ∈ Q_p
```

Where:
- `x_{n-k}`: The (n-k)-th digit in p-adic expansion
- `p`: Prime base
- `m`: Truncation parameter (partial sum vs. full sum)
- The exponent argument: `2π/p Σ_{k=0}^m x_{n-k}p^{-k}`

### P-Adic Valuation (Implicit Definition)

```
v(x) = position of first nonzero digit in p-adic expansion of x
     = min{n : x_n ≠ 0}
```

If x = 0, then v(0) = ∞ (and the sum becomes empty)

---

## 2. PARAMETER CONSTRAINTS - CRITICAL FOR SIERPINSKI STRUCTURE

### Theorem 6 (Page 6, Equation 20)

The mapping T_s^(m) becomes an **L-isometry** (true embedding preserving structure) when:

```
Δ_s^(m) > 0

where:
Δ_s^(m)/2 ≥ sin(π/p) - |s|/(1-|s|)

This requires:
|s| < s_0 = sin(π/p) / (1 + sin(π/p))
```

### For p = 3 (Sierpinski Triangle):
```
s_0 = sin(π/3) / (1 + sin(π/3))
    = (√3/2) / (1 + √3/2)
    = (√3/2) / ((2 + √3)/2)
    = √3 / (2 + √3)
    ≈ 1.732 / 3.732
    ≈ 0.4641
```

**CRITICAL**: This constraint MUST be satisfied for proper Sierpinski hierarchical structure.

### Complex Rotation Parameter

The paper does NOT explicitly state that s must have a specific argument/rotation. However:

From equation (17) on page 6:
```
T_s^(m)(px) = sT_s^(m)(x) + 1
```

This shows the scaling relationship. The complex value of s determines:
- Magnitude: Controls convergence and scaling (must satisfy |s| < s_0)
- Argument: Controls rotation/orientation of the fractal structure

For **p-fold symmetry** (especially Sierpinski triangles for p=3), theory suggests:
```
arg(s) = 2π/p  (or multiples thereof)
```

For p=3: arg(s) = 2π/3 = 120° creates triangular symmetry

---

## 3. FIGURE 4 REFERENCE - SIERPINSKI TRIANGLE EXAMPLE

The paper shows Figure 1.10 and Figure 1.12 (page 12) as key examples:

**Figure 1.10**: p=3, m=0, s=-1/2 **→ Sierpinski Carpet**
- Shows clean triangular hierarchical structure
- Black and white contrast
- Clear fractal boundaries

**Figure 1.12**: p=3, m=∞, s≈0.46 **→ SIERPINSKI TRIANGLE (GOAL)**
- Parameters: s_0 - 0.02 ≈ 0.246 (satisfies constraint)
- Shows clean point cloud forming triangular Sierpinski structure
- Complete p-adic space embedding (all 729 points for 3^6)
- Points clustered in hierarchical triangular pattern

---

## 4. COMPLETE ALGORITHM STEP-BY-STEP

### Input:
- `x`: Integer in [0, p^l)
- `p`: Prime base (typically 3)
- `l`: Depth (number of digits) - typically 6 for 3^6 = 729 points
- `s`: Complex parameter (magnitude < s_0, argument = 2π/p for symmetry)
- `m`: Truncation level for additive character (typically m = l for full depth)

### Algorithm:

```
1. Convert integer x to base-p digits (least significant first):
   digits = [x % p, (x // p) % p, ..., (x // p^(l-1)) % p]

2. Find p-adic valuation v(x):
   v = position of first nonzero digit
   if all zero: v = l (or return 0 for v=0 case)

3. Compute base term:
   if |1 - s| < 1e-14:
       base = v  (handle s ≈ 1)
   else:
       base = (1 - s^v) / (1 - s)

4. Initialize result:
   z = base

5. For each n from v to l-1:
       - Compute additive character argument:
           chi_arg = Σ_{k=0}^{min(m,n)} digit[n-k] * p^(-k)

       - Compute additive character:
           chi = exp(i * 2π/p * chi_arg)

       - Add scaled character to result:
           z += s^n * chi

6. Return z (complex number)

7. Convert to real/imaginary coordinates:
   x_coord = Re(z)
   y_coord = Im(z)
```

### Key Implementation Details:

1. **Digit Extraction**: Must be least-significant first
   ```python
   digits[i] = (x // (p**i)) % p
   ```

2. **Valuation Computation**: Position of first nonzero digit
   ```python
   v = next(i for i in range(l) if digits[i] != 0) else l
   ```

3. **Additive Character**: Exact formula with modular arithmetic
   ```python
   chi_arg = sum(digits[n-k] * (p**(-k)) for k in range(min(m+1, n+1) if n < len(digits)))
   chi = exp(1j * 2*pi/p * chi_arg)
   ```

4. **Base Term Handling**: Watch for s → 1 case
   ```python
   if abs(1 - s) < 1e-14:
       base = v
   else:
       base = (1 - s**v) / (1 - s)
   ```

---

## 5. CRITICAL PROPERTIES FROM THEOREM 6

If Δ_s^(m) > 0 (i.e., |s| < s_0), then:

1. **L-Isometry Property**: T_s^(m) preserves metric structure
2. **Hausdorff Dimension**: D_h(T_s^(m)(Q_p)) = D_s = -log_p(|s|)
3. **Measure Preservation**: Haar measure in Q_p maps to fractal measure
4. **Self-Similarity**: The set RanT_s^(m) is self-similar (Equation 18)

---

## 6. DIMENSIONAL ANALYSIS

From equation (17):
```
T_s^(m)(px) = sT_s^(m)(x) + 1
```

This defines the **scaling dimension**:
```
D_s = -log_p(|s|)
```

For p=3, |s|=0.246:
```
D_s = -log_3(0.246) ≈ 1.237
```

This fractional dimension is what creates the Sierpinski hierarchy.

---

## 7. EXAMPLES FROM PAPER

Figure 1 shows 12 different embeddings with parameters:

| Label | p | m | s | Structure |
|-------|---|---|---|-----------|
| 1.1 | 2 | 1 | 1/3 | Cantor Set |
| 1.10 | 3 | 0 | -1/2 | **Sierpinski Carpet** |
| 1.12 | 3 | ∞ | 0.46 | **Sierpinski Triangle** |

---

## 8. SPECIFIC PARAMETER SELECTION FOR SIERPINSKI

Based on the paper's examples and theory:

For **p=3, l=6** (complete 729-point space):
- **s_0 = 0.4641**
- **Recommended |s| = 0.9 * s_0 ≈ 0.4177** (but paper uses s=0.46 directly)
- **Recommended arg(s) = 2π/3 = 120°** (for triangular symmetry)
- **Recommended m = l = 6** (full depth truncation)

This creates:
- Stable embedding (|s| safely below s_0)
- 3-fold rotational symmetry for triangular pattern
- Full hierarchical structure across all 6 digit levels
- Complete Sierpinski triangle visible

---

## 9. KEY DIFFERENCES FROM DISPERSED IMPLEMENTATIONS

If you're seeing **dispersed points** instead of Sierpinski triangles, check:

1. **Parameter Constraint Violation**:
   - Is |s| ≥ s_0? → **BUG** (violates Theorem 6)
   - Solution: |s| < 0.4641 for p=3 (empirically, s=0.46 from paper works fine)

2. **Missing Complex Rotation**:
   - Is s purely real? → **Missing symmetry**
   - Solution: Set arg(s) = 2π/p for p-fold symmetry

3. **Wrong Additive Character**:
   - Are you summing the right digits?
   - Solution: Verify χ_n^(m) uses indices [n-k] from digits[n-k]

4. **Incorrect Valuation**:
   - Does it find the FIRST nonzero digit?
   - Solution: v = position, not count of zeros

5. **Missing or Wrong Base Term**:
   - Is the (1-s^v)/(1-s) term included?
   - Solution: This is essential for the embedding to work

6. **Wrong Digit Ordering**:
   - Are digits stored least-significant first?
   - Solution: digits[0] = x % p, digits[1] = (x//p) % p, etc.

---

## 10. VALIDATION CHECKLIST

✓ Algorithm matches Chistyakov equation (15) exactly
✓ Additive character implements equation (14) correctly
✓ Parameter constraint: |s| < s_0 = sin(π/p)/(1+sin(π/p))
✓ For p=3: |s| < 0.4641 (paper uses s=0.46 for Sierpinski triangle)
✓ Complex rotation: arg(s) = 2π/p for symmetry
✓ Valuation finds first nonzero digit position
✓ Base term: (1-s^v)/(1-s) included
✓ Character sum: Σ from v to l-1
✓ Digit extraction: least-significant first
✓ Truncation: m parameter applied correctly

---

## 11. WHEN APPLIED CORRECTLY

The embedding should show:
- **Complete 3^l point cloud** (all 729 for l=6)
- **Hierarchical clustering** into p (3) main groups at each level
- **Self-similar Sierpinski structure** visible
- **Triangular pattern** for p=3
- **NO scattered/dispersed points**
- **Clear boundaries** between hierarchical levels
- **White dots** (background p-adic space) less prominent
- **Black dots** (data pixels) forming fractal shape

---

## References Within Paper

- **Theorem 1**: Hausdorff measure inequalities (page 3)
- **Theorem 6**: L-isometry conditions (page 6) **← CRITICAL**
- **Theorem 7**: Measure coincidence with Haar measure (page 6)
- **Equation 15**: Main embedding formula (page 5)
- **Equation 14**: Additive character (page 5)
- **Equation 20**: Constraint inequality (page 6)
- **Figure 1.10**: Sierpinski carpet example (page 12)
- **Figure 1.12**: Sierpinski triangle example (page 12)


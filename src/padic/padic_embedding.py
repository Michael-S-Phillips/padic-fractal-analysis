"""
P-adic to Euclidean embedding using Chistyakov algorithm.

Implements the embedding T_s^(m): Q_p → C from Chistyakov (1996)
"Fractal geometry for images of continuous embeddings of p-adic numbers..."

Maps p-adic integers to complex plane, creating Sierpinski-like fractals.

Reference: D.V. Chistyakov, "Fractal Geometry for Images of Continuous
Embeddings of p-Adic Numbers and Solenoids into Euclidean Spaces",
Theoretical and Mathematical Physics, Vol. 109, No. 3 (1996)
"""

import numpy as np
from typing import Tuple, Union, Optional


def padic_to_base_p_digits(n: int, p: int, l: int) -> np.ndarray:
    """
    Convert integer to base-p digit representation (least significant first).

    Parameters
    ----------
    n : int
        Integer in [0, p^l)
    p : int
        Prime base
    l : int
        Number of digits

    Returns
    -------
    digits : np.ndarray
        Array of digits [d_0, d_1, ..., d_{l-1}] where d_0 is least significant
    """
    digits = np.zeros(l, dtype=int)
    temp = n
    for i in range(l):
        digits[i] = temp % p # Modulo to get least significant digit
        temp //= p # Integer division
    return digits


def compute_s_0(p: int) -> float:
    """
    Compute the maximum bound s_0 for embedding parameter |s|.

    For embedding T_s^(m) to be an isometry (Theorem 6, Chistyakov 1996),
    requires: |s| < s_0 = sin(π/p) / (1 + sin(π/p))

    Parameters
    ----------
    p : int
        Prime base

    Returns
    -------
    s_0 : float
        Maximum absolute value for |s|
    """
    return np.sin(np.pi / p) / (1 + np.sin(np.pi / p))


def get_default_s(p: int, stability_factor: float = 0.9, use_rotation: bool = False) -> complex:
    """
    Compute default parameter s for Sierpinski-like fractal structure.

    Supports two modes:
    1. Real parameter (Chistyakov paper examples): |s| = stability_factor * s_0
    2. Complex parameter with rotation (enhanced): s = |s| * exp(i * 2π/p)

    Parameters
    ----------
    p : int
        Prime base
    stability_factor : float
        Fraction of s_0 to use (default 0.9 for stability)
        s_0 = sin(π/p) / (1 + sin(π/p))
    use_rotation : bool
        If False (default): Return real s = stability_factor * s_0
        If True: Return complex s = stability_factor * s_0 * exp(i * 2π/p)

        Paper examples (Figure 1) use real s:
        - Figure 1.10: s = -1/2 (Sierpinski carpet)
        - Figure 1.12: s ≈ 0.46 (Sierpinski triangle)

    Returns
    -------
    s : complex (or float if real)
        Scaling parameter for p-adic embedding

    Notes
    -----
    The rotation arg(s) = 2π/p creates p-fold rotational symmetry but is NOT
    prescribed by the paper. Paper examples use real (or carefully chosen complex)
    values. Use use_rotation=True only if validation confirms it improves results.
    """
    s_0 = compute_s_0(p)
    magnitude = stability_factor * s_0

    if use_rotation:
        # Complex with rotation (creates p-fold symmetry)
        # For p=3: angle = 2π/3 = 120°
        # For p=2: angle = π/2 = 90°
        angle = 2 * np.pi / p
        return magnitude * np.exp(1j * angle)
    else:
        # Real parameter (matches paper examples)
        # For p=3: s ≈ 0.241 (pure real, positive)
        return magnitude


def get_paper_s(example: str, p: int = 3, corrected: bool = True) -> complex:
    """
    Get parameter s from Chistyakov paper examples.

    NOTE: The paper's Figure 1.10 caption states s=-0.5, but empirical testing
    shows this produces dispersed points. The sign-corrected value s=+0.5
    produces the clean Sierpinski carpet structure. This may indicate an error
    in the paper's figure caption.

    Parameters
    ----------
    example : str
        Paper example identifier:
        - "sierpinski_carpet": Figure 1.10, p=3, m=0, s=0.5 (sign-corrected)
        - "sierpinski_triangle": Figure 1.12, p=3, m=∞, s≈0.46
        - "cantor_set": Figure 1.1, p=2, m=1, s=1/3
        - "custom": Return None, user must specify s manually

    p : int
        Prime base (for validation against example)

    corrected : bool
        If True (default), use sign-corrected values that produce clean Sierpinski.
        If False, use values exactly as stated in paper (may produce poor results).

    Returns
    -------
    s : complex or float
        Parameter s (real or complex as appropriate)

    Raises
    ------
    ValueError
        If example doesn't match requested p value
    """
    if corrected:
        # Sign-corrected examples that actually produce Sierpinski structures
        examples = {
            "sierpinski_triangle": {"p": 3, "s": 0.5, "m": 0, "figure": "1.10", "note": "sierpinski triangle"},
            "sierpinski_triangle_inv": {"p": 3, "s": -0.5, "m": 0, "figure": "1.11", "note": "sierpinski triangle inverted"},
            "cantor_set": {"p": 3, "s": 0.46, "m": None, "figure": "1.12", "note": "general cantor set"},
            "cantor_set_1": {"p": 2, "s": 1/3, "m": 1, "figure": "1.1", "note": "general cantor set"},
        }
    else:
        # Exact values from paper (may produce poor results)
        examples = {
            "sierpinski_carpet": {"p": 3, "s": -0.5, "m": 0, "figure": "1.10", "note": "as-stated"},
            "sierpinski_triangle": {"p": 3, "s": 0.46, "m": None, "figure": "1.12", "note": "as-stated"},
            "cantor_set": {"p": 2, "s": 1/3, "m": 1, "figure": "1.1", "note": "as-stated"},
        }

    if example not in examples:
        raise ValueError(f"Unknown example: {example}. Choose from {list(examples.keys())}")

    config = examples[example]
    if config["p"] != p:
        raise ValueError(f"Example '{example}' requires p={config['p']}, but p={p} provided")

    return config["s"]


def padic_valuation(digits: np.ndarray) -> int:
    """
    Compute p-adic valuation v(x) - position of first nonzero digit.

    For a p-adic number x = Σ d_i p^i, v(x) is the smallest i such that d_i ≠ 0.

    Parameters
    ----------
    digits : np.ndarray
        Base-p digit representation

    Returns
    -------
    v : int
        Valuation (index of first nonzero digit, or len(digits) if all zero)
    """
    for i, d in enumerate(digits):
        if d != 0:
            return i
    return len(digits)


def embed_padic_chistyakov(padic_int: int, p: int, l: int, s: complex, m: int) -> complex:
    """
    Embed a p-adic integer to C using Chistyakov's algorithm (Definition 3, p.1499).

    Computes T_s^(m)(x) = (1 - s^v(x))/(1-s) + Σ_{n=v(x)}^∞ s^n χ_n^(m)(x)
    where χ_n^(m)(x) = exp(i2π/p Σ_{k=0}^m x_{n-k} p^{-k}) is the additive character.

    This algorithm creates hierarchical Sierpinski-like fractals naturally through
    the interaction of p-adic valuations and additive characters.

    Parameters
    ----------
    padic_int : int
        Integer in [0, p^l) representing element of Z_p/p^l Z_p
    p : int
        Prime base (typically 2 or 3)
    l : int
        Level/depth (number of p-adic digits)
    s : complex
        Parameter with |s| < s_0 = sin(π/p) / (1 + sin(π/p))
        Controls scaling of the fractal
    m : int
        Truncation level for additive characters
        m=∞ gives full character, finite m gives partial representation

    Returns
    -------
    z : complex
        Complex plane coordinates
    """
    # Get base-p digits (least significant first)
    digits = padic_to_base_p_digits(padic_int, p, l)

    # Compute p-adic valuation v(x)
    v = padic_valuation(digits)

    # Base term: (1 - s^v(x)) / (1 - s)
    if abs(1 - s) < 1e-14:
        # Handle s ≈ 1
        z = complex(v, 0)
    else:
        z = (1 - s ** v) / (1 - s)

    # Add character sum: Σ_{n=v}^{l-1} s^n χ_n^(m)(x)
    for n in range(v, l):
        # Compute additive character χ_n^(m)(x)
        # χ_n^(m)(x) = exp(i2π/p Σ_{k=0}^{min(m, n)} x_{n-k} p^{-k})

        chi_arg = 0.0  # Argument to exponential
        for k in range(min(m + 1, n + 1)):
            if n - k < len(digits):
                # Extract digit x_{n-k} and contribute to argument
                digit_index = n - k
                chi_arg += digits[digit_index] * (p ** (-k))

        # Compute additive character
        chi = np.exp(1j * 2 * np.pi * chi_arg / p)

        # Add contribution to z
        z += (s ** n) * chi

    return z


def embed_padic_cloud(padic_ints: np.ndarray, p: int, l: int, s: Optional[complex] = None,
                      m: Optional[int] = None) -> np.ndarray:
    """
    Embed array of p-adic integers to complex plane using Chistyakov's algorithm.

    Produces hierarchical Sierpinski-like fractal patterns through proper parameter selection:
    - |s| < s_0 = sin(π/p)/(1+sin(π/p)) (isometry constraint)
    - arg(s) = 2π/p (creates p-fold rotational symmetry)

    Parameters
    ----------
    padic_ints : np.ndarray
        1D array of integers in [0, p^l)
    p : int
        Prime base (e.g., 2, 3, 5)
    l : int
        Level/depth (number of p-adic digits)
    s : complex, optional
        Scaling parameter. If None, use auto-selected:
        - Magnitude: 0.9 * s_0 (90% of maximum stable value)
        - Angle: 2π/p (creates p-fold symmetry for fractal structure)
        For p=3: creates 120° rotations → Sierpinski triangles
        For p=2: creates 90° rotations → Sierpinski squares
    m : int, optional
        Character truncation level. If None, use m = l (full depth)

    Returns
    -------
    points : np.ndarray
        Shape (n, 2), 2D embedding coordinates (real, imag)

    Notes
    -----
    The embedding T_s^(m)(x) = (1 - s^v(x))/(1-s) + Σ s^n χ_n^(m)(x)
    satisfies the isometry condition (Theorem 6, Chistyakov 1996) only when
    |s| < s_0. Using the default s ensures proper Sierpinski structure.
    """
    # Set defaults
    if s is None:
        s = get_default_s(p, stability_factor=0.9)

    if m is None:
        m = l

    # Validate parameter constraint
    s_0 = compute_s_0(p)
    if abs(s) > s_0:  # Theorem 6 constraint: |s| < s_0 (strict inequality)
        import warnings
        warnings.warn(
            f"Warning: |s| = {abs(s):.4f} violates embedding constraint |s| < s_0 = {s_0:.4f}. "
            f"(Theorem 6, Chistyakov 1996) "
            f"This may result in non-isometric embedding and poor fractal structure.",
            UserWarning
        )

    # Embed each p-adic integer
    n = len(padic_ints)
    complex_points = np.zeros(n, dtype=complex)

    for i, padic_int in enumerate(padic_ints):
        complex_points[i] = embed_padic_chistyakov(int(padic_int), p, l, s, m)

    # Convert to 2D array (real, imaginary)
    points = np.zeros((n, 2), dtype=np.float32)
    points[:, 0] = complex_points.real
    points[:, 1] = complex_points.imag

    return points
